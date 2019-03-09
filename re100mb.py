# coding=utf-8
import re#gex as re
import os
import time
import hashlib

re_line = r'[-—=~～＝_…－＿]'
re_separater = re_line + r'{7,}'
re_longseparater = re_line + r'{16,}'
re_datetime = (r'\b\d{4}-\d{1,2}-\d{1,2}\s+'
               r'\d{1,2}:\d{1,2}(?::\d{1,2}(?:\.\d{0,4})?)?\b')
re_str = (r'(?:'
          r'(?:回复日期|提交日期|发表日期|时间|来自[^\n]{1,20})'
          r'(?:：|:)'
          r')'
          )

re_list = (     
            # test 1
            [
                (r'^\s*', re_separater, r'\s*'),
                0,
                r''
            ],
            
            # test 2
            [
                (r'\s*', re_separater, r'\s*$'),
                0,
                r''
            ],
            
            # test 3
            [
                (r'^\s+', re_separater, r'$'),
                re.M,
                r'==============='
            ],
            
            # test 4
            [
                (r'^', re_separater, r'\s+$'),
                re.M,
                r'==============='
            ],

            # test 5
            [
                (r'(?!<\n)(?<!', re_line , r')', 
                 re_longseparater, r'\n'),
                0,
                r'\n===============\n'
            ],

            # test 6
            [
                (r'^(?=(', re_separater, r'))'
                 r'\1'
                 r'(\S)'),
                re.M,
                r'===============\n\2'
            ],

            # test 7
            [
                (r'(?:', re_separater, r'\s+){2,}'),
                0,
                r'\n===============\n'
            ],
            
            # test 8
            [
                (r'(?<=\S)(?<!', re_line , r')',
                 r'(?=(', re_longseparater, r'))\1', 
                 r'(?=\S)'),
                0,
                r'\n===============\n'
            ],

            # test 9
            [
                (r'@(\S{1,16})\s+', re_str, r'?', re_datetime,
                 r'(?:\s+回复\b)?\s*'),
                0,
                r'@@\1##\n'
            ],

            # test 10
            [
                (r'@(\S{1,16})\s+\d+楼\s+(?:', re_datetime, r')?\s*'),
                0,
                r'@@\1##\n'
            ],

            # test 11
            [
                (r'(?:(?:(?:作?者|楼?主)(?:：|:))|^)\s*'
                 r'(\S{1,16})\s+',
                 re_str, r'?\s*', re_datetime, r'(?:\s+回复\b)?\s*'
                 ),
                re.M,
                r'@@\1##\n'
            ],

            # test 12
            [
                (r'回复第\d+楼\(作者:\s*@(\S{1,16})\s+于\s+',
                 re_datetime, r'\)\s*'),
                0,
                r'@@\1##\n'
            ],

            # test 13
            [
                r'回复第\d+楼，\s*@(\S{1,16})\b\s*',
                0,
                r'@@\1##\n'
            ],
            
            # test 14
            [
                (r'^(@@\S{1,16}##)\n',
                 r'(?!.*?@@\S{1,16}##)',
                 r'(?!.*?\n', re_separater, r'\s+)',
                 r'(.*)'),
                re.DOTALL,
                r'\1\n无内容\n==========\n\2'
            ],

            # test 15
            [
                (r'^(?!.*?@@\S{1,16}##)',
                 r'(?=(.*?\n', re_separater, r'\s+))'
                 r'(?!\1.*?\n', re_separater, r'\s+)',
                 r'\s*(.*?)\s*', re_separater, r'\s+(.*)'),
                re.DOTALL,
                r'@@000##\n\2\n==========\n\3'
            ],

            # test 16
            [
                (r'^(?=(.*@@(\S{1,16})##))',
                 r'\1',
                 r'.*?',
                 r'(?<=\n)',
                 r'(?=(.*?(?<=\n)', re_separater, r'\s+))',
                 r'(?!\3.*?(?<=\n)', re_separater, r'\s+)',
                 r'\s*(.*?)\s*', re_separater, r'\s+(.*)'),
                re.DOTALL,
                r'回复 \2：\n【引用开始】\4\n【引用结束】\n\5'
            ],
            )

def read_data():
    dir_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(dir_path, '100MB.txt')
    xz_path = os.path.join(dir_path, '100MB.txt.xz')

    # decompress 100MB.txt.xz at the first time
    if not os.path.isfile(file_path):
        import lzma

        with lzma.open(xz_path) as f:
            file_content = f.read()

        with open(file_path, 'wb') as f:
            f.write(file_content)

    # read data
    with open(file_path, encoding='gb18030') as f:
        txt = f.read()

    txt_lst = [m.group(1) for m in 
           re.finditer(r'(?s)\n<time>[^\n]*\n(.*?)\n<mark>', txt)]
    print('read %d pieces of text.' % len(txt_lst))

    # compile patterns
    for i in re_list:
        i[0] = ''.join(i[0])
        i.append(re.compile(i[0], i[1]))

    return txt_lst

def do_test(txt_lst):
    all_time = 0
    print('start 100MB test, please wait dozens of seconds.')

    for test_no, r in enumerate(re_list, 1):
        print('test %02d/%d, ' % (test_no, len(re_list)), end='', flush=True)
        t1 = time.perf_counter()

        for i in range(len(txt_lst)):
            txt_lst[i] = r[3].sub(r[2], txt_lst[i])

        t2 = time.perf_counter()
        all_time += t2 - t1
        print('%.3f sec.' % (t2-t1))

    print('100MB test finished, %.3f sec in all.' % all_time)
    
    # verify hash of generated data
    bytes_data = '⊕'.join(txt_lst).encode('gb18030')
    hash_md5 = hashlib.md5(bytes_data).hexdigest()
    hash_sha1 = hashlib.sha1(bytes_data).hexdigest()

    pre_computed_md5 = 'ad208a56a87fca2704da2dbe6d29b0ea'
    pre_computed_sha1 = 'b80558720298b088ab330e30dd62bfcebaa8e342'
    if hash_md5 != pre_computed_md5 or \
        hash_sha1 != pre_computed_sha1:
        print('ERROR: wrong data generated!')
    else:
        print('Generated data passed hash verification.')

def find_diff(txt_lst):
    import re
    import regex

    for test_no, r in enumerate(re_list, 1):
        for i in range(len(txt_lst)):
            r1 = re.sub(r[0], r[2], txt_lst[i], flags=r[1])
            r2 = regex.sub(r[0], r[2], txt_lst[i], flags=r[1])
            if r1 != r2:
                print('test %02d generates wrong data, abort.' % test_no)
                print(txt_lst[i])
                print()
                print(r1)
                print()
                print(r2)
                print()
                raise Exception()
            txt_lst[i] = r1

if __name__ == "__main__":
    txt_lst = read_data()
    do_test(txt_lst)
    #find_diff(txt_lst)
