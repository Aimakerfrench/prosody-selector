# -*- coding: utf-8 -*-

import itertools

# تعريف الخيارات الممكنة لكل كلمة في الشطر الأول
shatr1_options = [
    ["فَاْعِلَاْتُكَ", "فَاْعِلَاْتُنْ"],
    ["فَاْعِلَاْتُكَ", "فَاْعِلَاْتُنْ"],
    ["فَاْعِلَاْتُكَ", "فَاْعِلُنْ", "فَاْعِلَاْتُ"]       

           
]

shatr2_options = [
    ["فَاْعِلَاْتُكَ", "فَاْعِلَاْتُنْ"],
    ["فَاْعِلَاْتُكَ", "فَاْعِلَاْتُنْ"],
    ["فَاْعِلَاْتُكَ", "فَاْعِلُنْ", "فَاْعِلَاْتُ"]   
]

# توليد جميع التركيبات الممكنة للشطر الأول
shatr1_combinations = list(itertools.product(*shatr1_options))

# توليد جميع التركيبات الممكنة للشطر الثاني
shatr2_combinations = list(itertools.product(*shatr2_options))

# فتح ملف نصي لكتابة النتائج
with open('المتوافر التّامّ.txt', 'w', encoding='utf-8') as f:
    # المرور على جميع التركيبات الممكنة
    for comb1 in shatr1_combinations:
        for comb2 in shatr2_combinations:
            line = ' '.join(comb1) + ' *** ' + ' '.join(comb2)
            f.write(line + '\n')

print("انتهى.txt")
