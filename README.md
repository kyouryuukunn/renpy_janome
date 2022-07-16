 折り返しはノベルゲームの読み易さに直結しますが、直接ゲーム画面を確認するには作業が膨大すぎます。
 本ライブラリでは形態要素解析ソフトjanomeにより折り返しキャッシュを生成し、Ren'Pyで日本語文法を考慮した自動折り返しを行ないます。
 例えば標準の"japanese-strict"での折り返しでは1つ目の画面だったのが、本ライブラリを使用すると2つ目の画面になります。

 japanese-strict
![Demo](https://dl.dropboxusercontent.com/s/m53lhuy5dubkn5t/japanese-strict.png)
 janome
![Demo](https://dl.dropboxusercontent.com/s/97pqwvzoq97id1p/janome.png)

 Janome <https://mocobeta.github.io/janome/>

 Janomeによる解析はそれなりに重い処理になります。PC上では問題にならないでしょうが、mobile環境やweb版では動作が不安定化するため、本ライブラリではユーザー環境ではリアルタイム解析をさせず、予め生成したキャッシュを活用します。ファイルサイズがテキストファイル分増加しますが、現代の環境では問題ないでしょう。また、配布するのはキャッシュ結果のみなのでjanomeおよびjanomeの辞書を配布物に含める必要はありません。

 使用方法:

 1. janome.rpyをgameフォルダにコピーしてください。
 2. janomeをrenpy/lib/python3.x 以下に配置してください。通常サードパーティーライブラリはgameフォルダに配置するべきですが、janomeの場合どうも直接本体に入れないと動作しませんでした。本ファイルに含まれるjanomeフォルダ(v0.4.2)をコピーするか以下のようにpip install を使用してください。pip install でダウンロードすると "Janome-X.X.X.dist-info" と "bin" フォルダも作成されますが、ややこしいので "janome" フォルダ以外は削除してください。

    pip install --target (PATH) janome 


 例えば"E:\Soft"にrenpyをインストールしていて、"tutorial"で本ライブラリを使用するならばインストール後は以下のような構成になるはずです。

    E:\Soft\renpy\lib\python3.9\janome
    E:\Soft\renpy\tutorial\game\janome.rpy

 3. ランチャーから"台詞の抽出(Extract Dialogue)"を選択し、以下の設定で続行を押してください。

  * フォーマットは"台詞のテキストのみ(dialogue.txt)"
  * "台詞からテキストタグを取り除く" をチェック
  * "引用符や他の特殊文字をエスケープする" のチェックを外す
  * "台詞だけでなく飜訳可能なすべての文字列を抽出する" 台詞以外のキャッシュも生成したければチェック
  * Language はキャッシュ生成対象の言語にしてください。なお、日本語以外での使用は想定していません。"tutorial"の場合は"japanese", デフォルトが日本語なら"None"です。
![Demo](https://dl.dropboxusercontent.com/s/14yc69fhgbppduv/extract_dialogue.png)

 4. gameフォルダと同じフォルダにdialogue.txtが生成されたことを確認し、内容を確認してください。この情報を元にキャッシュを生成するため、ここの文字列は出来るだけゲーム画面に表示されるテキストそのままであることが望ましいです。

 ここで、"あなたは[player]です。" のように変数でテキストを置換しているとファイル上のテキストと画面に表示されるテキストが一致しなくなります。
 このような場合に対処するため、[]を使用している場合はテキストを "あなたは" と "です。" に分割してそれぞれでキャッシュを生成し、元のテキストと完全一致しなくとも一致した部分にキャッシュを適用するようにしています。テキスト全体の8割以上にキャッシュが適用できればOKとしていますが、アバウトな判定基準なので誤動作が予想されます。そういった部分のテキストにはjanomeを使用しないまたは、リリース前によくテストしてください。
 suffix, prefixで"「」"を追加していたり、extend ステートメントを使用している場合でも同様の処理で対処しています。

 v8.1.0.22071201n 現在,台詞の抽出で{{や%%のあるテキストがちゃんと生成されませんが、報告を上げたのでそのうち直ると思います。

 5. ゲームを起動して<Shift+O>でコンソールを開き \_janome.generate_janome_cache()を実行してください。
 dialogue.txtからキャッシュを生成しており、それなりに時間がかかります。実行後gameフォルダに"janome_cache.rpy"が生成されていることを確認してください。
 このファイルにはテキスト文字列と数値のタプルの辞書が定義されており、そのテキストは数値の文字の前で折り返しが許可されます。

 6. janome.rpyを開いて10行目のonly_cacheのオプションを必要に応じて変更してください。ユーザー環境と同じ状態でテストするため Trueのままを推奨します。
 Falseにするとconfig.developerがTrueで該当するキャッシュjがなければjanomeでリアルタイム解析をして自動折り返しを行ないます。
 Trueなら"japanese-strict"で代用します。

 7. 以下のように既存の折り返し関数をjanomeで上書きしてください。annotate_unicode以外であればどれでもよいですが、使用しないだろう annotate_westernを推奨します。
 これによりlanguageスタイルプロパティーに"western"を指定したテキストには"western"ではなくjanomeによる折り返しが行なわれます。:


    init python:
        renpy.text.textsupport.annotate_western = _janome.annotate_janome

 8. janomeによる折り返しを使用したいテキストのスタイルに7. で設定したlanguageスタイルプロパティーを設定してください。
 例えばadvやnvlウィンドウのテキストならばsay_dialogueとnvl_dialogue テキスト履歴はhistory_textになります。<Shift+i>で使用できるstyle インスペクターでスタイル名は分かります。
 影響が大きすぎるのでdefaultスタイルの変更は非推奨です。:


    init python:
        style.say_dialogue.language = "western"
        style.nvl_dialogue.language = "western"
        style.history_text.language = "western"

 9. これで8. で設定したテキストの折り返しで文法を考慮した折り返しが実施されるはずです。ゲームのリリース時にはjanome.rpycとjanome_cache.rpycを配布物に含めてください。
 また、配布物のビルド前にrenpy本体にコピーしたjanomeフォルダは削除してください。ここにファイルがあるとPC版では一緒に配布されてしまい、Android版ではエラーでビルドできなくなるようです。

 ライセンスについて

 本ライブラリを使用したゲームをリリースする場合、janomeもMeCap-IPADICも配布物には直接含まないはずで、含むのはそれらの結果を解析したキャッシュデータだけなのですがこの場合ライセンスどうすればいいのでしょうね？
 詳しい人教えて。

 
折り返しアルゴリズムについて
============================
後にくるのが助詞または助動詞でなければ助詞、または接続詞の後ろで折り返し許可をしています。


ライセンス
==========
 本来ライブラリではjanomeおよびMeCab-IPADIC dictionary/statistical modelを使用しています。ライセンスファイルはJanome-0.4.2.dist-infoに含まれています。

 * Janome <https://mocobeta.github.io/janome/>
 * MeCab-IPADIC dictionary/statistical model

 動作環境
=========

 動作確認は以下の環境で行なっています。Ren'Py v7系および v8.0以前では動作しません。

 * Ren'Py v8.1.0.22071201n
 * Janome v0.4.2
