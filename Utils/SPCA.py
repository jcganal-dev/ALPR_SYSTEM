import itertools
try:
    import Utils.check_helpers as helper
except ImportError:
    import check_helpers as helper
try:
    import Utils.DatabaseManager as DB
except ImportError:
    import DatabaseManager as DB
import time

class SPCA():
    def __init__(self,db_table:str,name:str):
        self.registered_plates = {}
        self.db_table = db_table
        self.name = name
        self.read_blacklist_file()

    def read_blacklist_file(self):
        registered_plates = self.registered_plates
        registered_plates.clear()
        try:
            result = DB.db.database_query(f"SELECT `plate_number`,IF(`first_name`= '', `last_name`, CONCAT(`last_name`, ', ' , `first_name`)) as 'full_name' FROM `{self.db_table}`")[1]
            for item in result:
                fullname = item['full_name'] if item['full_name'] != None else 'N/A'
                plate =item['plate_number']
                if fullname.strip()[0] == "#":
                    continue
                registered_plates[plate] = fullname
        except:
            print(f"Error! Cannot get list from ${self.db_table}")

    def check_registration(self,
                        plate:str,
                        pattern_check=False,
                        prints=True,
                        inner_trig=False,
                        advance_patterns=False):
        """ Checks database for plate text matches """
        start_time = time.perf_counter()
        plate = ''.join(plate.split(' '))
        plate = ''.join(plate.split('-'))
        if len(plate) < 5:
            return (False, plate, plate, 'N/A', 'N/A')
        
        # Base check (perfect match)
        owner = self.registered_plates.get(plate.upper())
        if owner != None:
            if not inner_trig and prints:
                print(f'{self.name} for {plate} read perfectly! took {(time.perf_counter()-start_time)*1000:.2f}ms (Perfect)')
            return (True, plate, plate, 'Perfect', owner)
        
        # Trimmed Logic 1983IHTL
        trimmed_plate_list = [plate]

        for p in range(1, 4):
            # Cut p characters from the right
            cut_right = plate[:-p]
            if len(cut_right) > 5:
                trimmed_plate_list.append(cut_right)
                
            # Cut p characters from the left
            cut_left = plate[p:]
            if len(cut_left) > 5:
                trimmed_plate_list.append(cut_left)
                
            # Cut p characters from both sides
            cut_both = plate[p:-p]
            if len(cut_both) > 5:
                trimmed_plate_list.append(cut_both)

        for trimmed_plate in trimmed_plate_list:
            owner = self.registered_plates.get(trimmed_plate)
            if owner != None:
                print(f'{self.name} for {plate} into {trimmed_plate} took {(time.perf_counter()-start_time)*1000:.2f}ms (Trimmed)')
                return (True, trimmed_plate, plate, 'Trimmed', owner)

        # Pattern Check Logic
        if pattern_check:
            if advance_patterns and prints and not inner_trig:
                print(f'Notice: BlackList Pattern Check is now using ADVANCE PATTERNS!')
            all_valid_combinations = set()
            
            for trimmed_plate in trimmed_plate_list:
                possible = False
                for plate_pattern in helper.plate_patterns:
                    if len(plate_pattern) == len(trimmed_plate):
                        possible = True
                        break
                if not possible:
                    continue
                possible_chars_list = []
                for char in trimmed_plate:
                    possibilities = {str(char)} 
                    char_str = str(char)
                    
                    num2let = helper.num2let.copy()
                    let2num = helper.let2num.copy()
                    let2let = helper.let2let.copy()
                    if advance_patterns:
                        num2let.extend(helper.num2let_adv)
                        let2num.extend(helper.let2num_adv)
                        let2let.extend(helper.let2let_adv)

                    subs_n2l = helper.find_all_in_tuples(char_str, num2let)
                    possibilities.update(subs_n2l)
                    subs_l2n = helper.find_all_in_tuples(char_str, let2num)
                    possibilities.update(subs_l2n)
                    subs_l2l = helper.find_all_in_tuples(char_str, let2let)
                    possibilities.update(subs_l2l)

                    possible_chars_list.append(list(possibilities))
                    
                raw_combinations = itertools.product(*possible_chars_list)
                valid_combinations = set()
                for combo_tuple in raw_combinations:
                    combo_string = "".join(combo_tuple)
                    string_pattern = helper.get_string_pattern(combo_string)
                    
                    if string_pattern in helper.plate_patterns:
                        valid_combinations.add(combo_string)
                all_valid_combinations = all_valid_combinations.union(valid_combinations)
            
            for reading in all_valid_combinations:
                if reading.upper() == plate.upper():
                    continue
                registered, reg_plate_found, _, _, owner = self.check_registration(reading, pattern_check=False, inner_trig=True)
                if registered:
                    if prints and not inner_trig:
                        print(f'{self.name} for {plate} into {reg_plate_found} took {(time.perf_counter()-start_time)*1000:.2f}ms (Pattern-checked)')
                    return (True, reg_plate_found, plate, 'Pattern-checked', owner)
                    
        if prints and not inner_trig:
            print(f'{self.name} for {plate} found NO MATCH! took {(time.perf_counter()-start_time)*1000:.2f}ms')
        return (False, plate, plate, 'N/A', 'N/A')

BlackListCheck = SPCA(db_table='unregistered_plates',name='BlackListCheck')
RegCheck = SPCA(db_table='registration_table',name='RegCheck')

if __name__ == "__main__":
    # A6280J
    registered, reading, plate, method, owner = BlackListCheck.check_registration('AITO1U', pattern_check=True, advance_patterns=False)
    print('Registered' if registered else 'Not registered')
    print(f'Reading: {reading}')
    print(f'Method: {method}')
    print(f'Owner: {owner}')