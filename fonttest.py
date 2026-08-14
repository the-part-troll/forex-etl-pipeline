#import matplotlib
#print(matplotlib.get_cachedir())

import matplotlib.font_manager as fm

font_list = [f.name for f in fm.fontManager.ttflist]
# 筛选包含中文相关字体
for name in sorted(set(font_list)):
    if "WenQuan" in name or "Hei" in name or "Sim" in name:
        print(name)
