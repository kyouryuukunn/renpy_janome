# init python:
#     renpy.text.textsupport.annotate_western = _janome.annotate_janome
init -3 python in _janome:
    janome_cache = {}

init -1 python in _janome:
    # Falseなら、config.developerがTrueでキャッシュされていなければリアルタイム解析を行なう
    # Trueなら、config.developerがTrueでもキャッシュ時以外でjanomeをリアルタイムで使用しない
    # config.developerがFalseの場合は常にリアルタイムを使用しない
    only_cache = True

    import os

    def init_janome():
        global janome_cache, janome_tokenize

        if renpy.config.developer and not only_cache:
            from janome.tokenizer import Tokenizer
            janome_tokenize = Tokenizer().tokenize
        else:
            janome_tokenize = None

    init_janome()


    def generate_janome_cache():
        global janome_tokenize

        if janome_tokenize is None:
            from janome.tokenizer import Tokenizer
            janome_tokenize = Tokenizer().tokenize

        global janome_cache
        janome_cache = {}

        org_file = os.path.join(renpy.config.basedir, "dialogue.txt")
        f = open(org_file, "r")
        org_text = f.read().split("\n")

        for line in org_text:
            #0x200bのみ含み一文字は折り返しの必要がない
            if len(line) > 1:
                #[]で置換される文は[]を境に分割して解析、キャッシュする
                split_start_pos = [0]
                split_end_pos = []
                in_substitution_depth = 0
                skip_flag = False
                for i, s in enumerate(line):
                    if skip_flag:
                        skip_flag = False
                        continue
                    if s == "[":  #]"
                        if i < len(line)-1 and line[i+1] != "[": #]"
                            in_substitution_depth += 1
                            split_end_pos.append(i)
                        else:
                            skip_flag = True
                    elif s == "]" and in_substitution_depth > 0:
                        in_substitution_depth -= 1
                        if i < len(line) - 1:
                            split_start_pos.append(i+1)

                if len(split_start_pos) != len(split_end_pos):
                    split_end_pos.append(len(line))

                for i, j in zip(split_start_pos, split_end_pos):
                    cached_text = line[i:j]
                    if len(cached_text) > 1:
                        janome_cache[cached_text] = _annotate_janome(cached_text, True)
        f.close()

        cache_file = os.path.join(renpy.config.basedir, "game", "janome_cache.rpy")
        f = open(cache_file, "w")
        f.write("init -2 python in _janome:\n")
        f.write("    janome_cache = " + str(janome_cache))
        f.close()

    def annotate_janome(glyphs, *args):
        SPLIT_NONE = 0
        SPLIT_BEFORE = 1

        if not glyphs:
            return

        if glyphs[0].character == 0x200b and len(glyphs) == 1:
            return

        text=""
        for g in glyphs:
            text += chr(g.character)

        cached = False

        split_pos = janome_cache.get(text, None)
        if split_pos is not None:
            for i in split_pos:
                glyphs[i].split = SPLIT_BEFORE
            cached = True

        if not cached:
            #extend, prefix, suffix, 置換文字その他に対応するため部分一致するキャッシュデータを使用する
            #誤作動に注意
            split_pos = set()
            cached_text = set()
            for k, v in janome_cache.items():
                if len(k) < len(text):
                    index = text.find(k)
                    if index >= 0:
                        cached_text.update(range(index, index+len(k)))
                        for i in v:
                            split_pos.add(index+i)
                            
                    #9割以上キャッシュが使えれば最後まで処理しない
                    if float(len(cached_text)) / len(text) > 0.9:
                        cached = True
                        break
            else:
                #8割以上キャッシュが使えれば十分とする
                if float(len(cached_text)) / len(text) > 0.8:
                    cached = True

            if cached:
                # "てすと。[player]です。" のように廉潔部分末尾で句読点があると折り返せない
                # その他後加工での不具合対策のため一部一致でのキャッシュ使用時は再度禁則処理する。
                old_g = glyphs[0]
                for i in range(len(glyphs)):
                    g = glyphs[i]

                    old_g_character_code = old_g.character
                    old_g_character = chr(old_g_character_code)
                    g_character_code = g.character
                    g_character = chr(g_character_code)

                    # split after a particle.
                    if i in split_pos:
                        g.split = SPLIT_BEFORE

                    # characters allowed to be placed at the end of a line 
                    if old_g_character in \
                        ")]）｝〕〉》」』】〙〗｠" \
                        "?!？！‼⁇⁈⁉" \
                        "、。":
                        g.split = SPLIT_BEFORE

                    # characters aren't placed at the begining of a line. 
                    # 0x00 is Null
                    if g_character_code == 0 or g_character in \
                        ",)]）｝、〕〉》」』】〙〗〟’”｠»" \
                        "ゝゞァィゥェォッャュョヮヵヶぁぃぅぇぉっゃゅょゎゕゖㇰㇱㇲㇳㇴㇵㇶㇷㇸㇹㇷ゚ㇺㇻㇼㇽㇾㇿ々〻" \
                        "ー‐゠–〜～" \
                        "?!‼⁇⁈⁉" \
                        "・:;/" \
                        "。." \
                        "？！":
                        g.split = SPLIT_NONE

                    old_g = g

        if cached:
            annotate_cached(glyphs)
            # pos = []
            # for g in glyphs:
            #     if g.split == SPLIT_BEFORE:
            #         pos.append(chr(g.character))
            # print(text, pos)
        elif renpy.config.developer and not only_cache:
            _annotate_janome(glyphs)
        else:
            # japanese-strict
            renpy.text.textsupport.annotate_unicode(glyphs, False, 3)


    def annotate_cached(glyphs):

        # can't import
        SPLIT_NONE = 0
        SPLIT_BEFORE = 1
        SPLIT_INSTEAD = 2
        RUBY_NONE = 0
        RUBY_BOTTOM = 1
        RUBY_TOP = 2
        RUBY_ALT = 3

        if not glyphs:
            return

        # Deal with ruby, by marking it as non-spacing.
        old_g = glyphs[0]
        old_g.split = SPLIT_NONE

        for g in glyphs:

            if g.character == 0:
                g.split = SPLIT_BEFORE

            if g.character == 0x20 or g.character == 0x200b:
                g.split = SPLIT_INSTEAD

            if g.ruby == RUBY_TOP or g.ruby == RUBY_ALT:
                g.split = SPLIT_NONE

            elif g.ruby == RUBY_BOTTOM and old_g.ruby == RUBY_BOTTOM:
                g.split = SPLIT_NONE

            old_g = g
        glyphs[0].split = SPLIT_NONE  # SPLIT_INSTEAD only strings causes crash.


    def _annotate_janome(glyphs, cache=False):
        """
        Annotate the characters with line splitting information by janome.
        https://github.com/mocobeta/janome
        """
        # cdef Glyph g, old_g
        # cdef set particle_pos
        # cdef list word_formclass
        # cdef int split_flag
        # cdef int pos
        # cdef unicode org_text
        # cdef list split_pos
        # cdef split_t split_info

        # can't import
        SPLIT_NONE = 0
        SPLIT_BEFORE = 1
        SPLIT_INSTEAD = 2
        RUBY_NONE = 0
        RUBY_BOTTOM = 1
        RUBY_TOP = 2
        RUBY_ALT = 3

        particle_pos = set()
        split_flag = 0
        org_text = ""
        split_pos = []

        if not glyphs:
            return

        if cache:
            org_text = glyphs
        else:
            for g in glyphs:
                org_text += chr(g.character)

        pos = 0
        # The first and end hankaku and zenkaku spaces is not returned by tokenize.
        for i in org_text:
            if i in (" ", "　"):
                pos += 1
            else:
                break

        tokens = janome_tokenize(org_text)

        particle_pos_add = particle_pos.add
        # get the position set of characters after particles.
        for token in tokens:
            word_formclass = str(token).split(',')[0].split()

            if len(word_formclass) > 1:
                word, formclass = word_formclass
            else:
                word = " "
                formclass = word_formclass

            if split_flag == 1 and formclass not in ("助詞", "助動詞"):
                #助詞が続くときは最後の助詞で折り返す ex: 庭には
                particle_pos_add(pos)

            pos += len(word)
            if formclass in ("助詞", "接続詞"):
                split_flag = 1
            else:
                split_flag = 0

        old_g = glyphs[0]
        for i in range(len(glyphs)):
            g = glyphs[i]
            split_info = SPLIT_NONE

            if cache:
                old_g_character = old_g
                old_g_character_code = ord(old_g)
                g_character = g
                g_character_code = ord(g)
            else:
                old_g_character_code = old_g.character
                old_g_character = chr(old_g_character_code)
                g_character_code = g.character
                g_character = chr(g_character_code)

            # split after a particle.
            if i in particle_pos:
                split_info = SPLIT_BEFORE

            # characters allowed to be placed at the end of a line 
            if old_g_character in \
                ")]）｝〕〉》」』】〙〗｠" \
                "?!？！‼⁇⁈⁉" \
                "、。":
                split_info = SPLIT_BEFORE

            # characters aren't placed at the begining of a line. 
            # 0x00 is Null
            if g_character_code == 0 or g_character in \
                ",)]）｝、〕〉》」』】〙〗〟’”｠»" \
                "ゝゞァィゥェォッャュョヮヵヶぁぃぅぇぉっゃゅょゎゕゖㇰㇱㇲㇳㇴㇵㇶㇷㇸㇹㇷ゚ㇺㇻㇼㇽㇾㇿ々〻" \
                "ー‐゠–〜～" \
                "?!‼⁇⁈⁉" \
                "・:;/" \
                "。." \
                "？！":
                split_info = SPLIT_NONE

            # 0x20 is space, 0x200b is invisible space
            if g_character_code == 0x20 or g_character_code == 0x200b:
                split_info = SPLIT_INSTEAD

            if cache:
                if split_info == SPLIT_BEFORE:
                    split_pos.append(i)
            else:
                g.split = split_info

                # Don't split ruby.
                if g.ruby == RUBY_TOP or g.ruby == RUBY_ALT:
                    g.split = SPLIT_NONE
                elif g.ruby == RUBY_BOTTOM and old_g.ruby == RUBY_BOTTOM:
                    g.split = SPLIT_NONE

            old_g = g

        if cache:
            # A{rt}test[/rt] Aの後ろに0x200bがくるとルビが正常に
            # 表示できない。Aは通常名詞なので問題になる可能性は少ない
            # extend, prefix, suffixその他ファイルの文字列と変更されると動作しない
            # 末尾に追加されると判別もできない
            # 末尾に0x200bを追加してキャッシュ有無を判断
            # annotate関数内では文字を変更できない
            return tuple(split_pos)
        else:
            glyphs[0].split = SPLIT_NONE  # SPLIT_INSTEAD only strings causes crash.

    # def test(line):
    #     split_start_pos = [0]
    #     split_end_pos = []
    #     in_substitution_depth = 0
    #     skip_flag = False
    #     for i, s in enumerate(line):
    #         if skip_flag:
    #             skip_flag = False
    #             continue
    #         if s == "[":  #]"
    #             if i < len(line)-1 and line[i+1] != "[": #]"
    #                 in_substitution_depth += 1
    #                 split_end_pos.append(i)
    #             else:
    #                 skip_flag = True
    #         elif s == "]" and in_substitution_depth > 0:
    #             in_substitution_depth -= 1
    #             if i < len(line) - 1:
    #                 split_start_pos.append(i+1)
    #
    #     if len(split_start_pos) != len(split_end_pos):
    #         split_end_pos.append(len(line))
    #
    #     print(split_start_pos, split_end_pos)
    #     for i, j in zip(split_start_pos, split_end_pos):
    #         cached_text = line[i:j]
    #         print(cached_text)

    # def test(line):
    #
    #     from janome.tokenizer import Tokenizer
    #     janome_tokenize = Tokenizer().tokenize
    #
    #     tokens = janome_tokenize(line)
    #     for t in tokens:
    #         print(t)
