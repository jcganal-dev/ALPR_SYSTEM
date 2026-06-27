plate_patterns = [
    'NNNLLL',
    'LNNNNL',
    'NNNNNN',
    'LNNNLL',
    'NNNNLL',
    'LLNNNNN',
    'LLLNNNN',
    'LLLNNN'
]

num2let = [
    ('1', 'I'), ('2', 'Z'), ('3', 'B'), ('4', 'A'), ('5', 'S'),
    ('7', 'T'), ('8', 'B'), ('0', 'O'),
    ('0', 'Q'), ('0', 'D'), ('9', 'Y'), ('1', 'T'),

]

num2let_adv = [
    ('0', 'A'),
    ('1', 'D'),
    ('6', 'A'),
    ('9', 'O'),
    ('6', 'O'),
]

let2num = [
    ('A', '4'), ('B', '8'), ('D', '0'),
    ('I', '1'), ('O', '0'), ('Q', '0'), ('S', '5'), ('T', '7'), 
    ('Z', '2'), ('Q', '0'), ('D', '0'), ('G', '6')
]

let2num_adv = [
    ('Y', '9'), 
    ('V', '9'),
    ('C', '0'),
    ('G', '0'),
]

let2let = [
    ('W', 'V'), ('D', 'O'), ('X', 'Y'), ('D', 'B'),
    ('K', 'X'), ('Y', 'K'), ('O', 'Q'), ('M', 'N'), ('O', 'D'),
    ('L', 'I'), ('T', 'I'),
    ('H', 'M'), ('V', 'Y'), ('H', 'N'),
    ('N', 'A'), ('K', 'H'), ('11','M'),
    ('C', 'G'),
]

let2let_adv = [
    ('H', 'W'), # actual 890IBH (No Gate Pass), read as 896IBH, into 896IBW (Registered)
    ('U', 'N'),
    ('R', 'N'), 
    ('M', 'W'),
    ('O', 'A'),
    ('H', 'A'),
]

def get_string_pattern(s):
    pattern = ""
    for char in s:
        char_str = str(char)
        if char_str.isdigit():
            pattern += "N"
        elif char_str.isalpha():
            pattern += "L"
        else:
            pattern += "?" 
    return pattern

def find_all_in_tuples(char_to_find, tuple_list):
    """
    Searches a list of tuples and returns a LIST of ALL substitutions.
    Automatically checks both directions for interchangeable characters.
    """
    results = []
    char_str = str(char_to_find)
    for key, value in tuple_list:
        if str(key) == char_str:
            results.append(str(value))
        elif str(value) == char_str:
            results.append(str(key))
    return list(set(results))