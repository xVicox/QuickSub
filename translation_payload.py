class TranslationPayload:

    def __init__(self, path, dir_path, source_lang, target_lang):
        self._file_path = path
        self._dir_path = dir_path
        self._source_lang = self.map_languages(source_lang)
        self._target_lang = self.map_languages(target_lang)

        self._language_map = {
            "English" : "en",
            "Српски" : "sr"
        }

    def get_path(self):
        return self._file_path

    def get_dir_path(self):
        return self._dir_path

    def get_source_lang(self):
        return self._source_lang

    def get_target_lang(self):
        return self._target_lang

    @staticmethod
    def map_languages(user_friendly_lang_form):
        if user_friendly_lang_form == "English":
            return "en"
        elif user_friendly_lang_form == "Српски":
            return "sr"
        else:
            return "unknown"