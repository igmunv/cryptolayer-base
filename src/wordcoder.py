

class WordCoder:


    dictionary = None
    reverse_dictionary = None


    def __init__(self, dictionary: dict):
        # слова в словаре не должны быть больше 10 символов
        self._check_dict(dictionary)
        self.dictionary = {int(k, 16): v for k, v in dictionary.items()}
        self.reverse_dictionary = {v: int(k, 16) for k, v in dictionary.items()}


    def _check_dict(self, dictionary):

        for key in dictionary:
            if len(dictionary[key]) > 10:
                raise TypeError("Word size > 10 char")

        words = list(dictionary.values())

        if len(words) != len(set(words)):
            duplicates = []

            seen = set()
            for word in words:
                if word in seen:
                    duplicates.append(word)
                else:
                    seen.add(word)

            raise ValueError(
                f"Duplicates in WordCoder dictionary: {', '.join(sorted(set(duplicates)))}"
            )


    def encode(self, bytes_array: bytes):
        result = []
        for byte in bytes_array:
            result.append(self.dictionary[byte])
        return result


    def decode(self, words: list):
        result = []
        for word in words:
            result.append(self.reverse_dictionary[word])
        return bytes(result)
