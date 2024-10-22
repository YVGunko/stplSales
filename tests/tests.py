import unittest

def extract_substring(input_str):
    """Extract substring from input string up to the first space, after trimming."""
    input_str = input_str.strip()  # Trim leading and trailing whitespace
    first_space_index = input_str.find(' ')
    return input_str[:first_space_index] if first_space_index != -1 else input_str


class Test_substring(unittest.TestCase):

    def test_extract_substring(self):
        test_cases = [
            ("АДВЕНТУРА-КИДС №9/№11 МАТ.ТЕРТ 37 Р", "АДВЕНТУРА-КИДС"),  # No spaces
            ("АДВЕНТУРА КИДС №9/№11", "АДВЕНТУРА"),        # Single space
            (" ADVENTURA-KIDS is great", "ADVENTURA-KIDS"),  # No space before
            ("  ADVENTURA KIDS", "ADVENTURA"),      # Leading spaces
            ("ADVENTURA KIDS is great", "ADVENTURA"),  # Space in the middle
            ("KIDS ADVENTURA", "KIDS"),              # Starts with a different word
            ("", ""),                                  # Empty string
        ]

        for input_str, expected in test_cases:
            result = extract_substring(input_str)
            self.assertEqual(result, expected, f"Failed for input '{input_str}'. Expected '{expected}', got '{result}'.")

if __name__ == '__main__':
    unittest.main()

