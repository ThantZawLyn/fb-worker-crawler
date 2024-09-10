import re


def string_count_to_int(count):
    try:
        if count is None or len(count) == 0:
            return 0
        if type(count) == float or type(count) == int:
            return count
        if 'others' in count:
            count = count.split(" ")[-2]
            if 'K' in count:                
                if len(count) > 1:                    
                    return int(float(count.replace('K', '')) * 1000)               
            if 'M' in count:
                if len(count) > 1:
                    return int(float(count.replace('M', '')) * 1000000)
            if 'B' in count:
                if len(count) > 1:
                    return int(float(count.replace('B', '')) * 1000000000)                   
            return int(count)
        if not 'others' in count:
            count = count.split(" ")[0]
            if 'K' in count:                
                if len(count) > 1:                    
                    return int(float(count.replace('K', '')) * 1000)               
            if 'M' in count:
                if len(count) > 1:
                    return int(float(count.replace('M', '')) * 1000000)
            if 'B' in count:
                if len(count) > 1:
                    return int(float(count.replace('B', '')) * 1000000000)                   
            return int(count)
    except Exception as e:
        return int(to_float(count))


def to_float(count):
    return float(re.findall(r'[\d\.\d]+', count)[0])


def to_int(count):
    return int(re.findall(r'[\d\.\d]+', count)[0])



