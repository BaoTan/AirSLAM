import csv
import os

# 提示用户输入 CSV 文件的路径
input_csv = input("请输入 CSV 文件的路径: ")

# 获取输入文件的父目录
parent_dir = os.path.dirname(input_csv)

# 构建输出文件的路径
output_txt = os.path.join(parent_dir, "gt_tum.txt")

# 打开输入 CSV 文件和输出 TXT 文件
with open(input_csv, 'r', newline='') as csvfile, open(output_txt, 'w') as txtfile:
    # 创建 CSV 读取器
    reader = csv.reader(csvfile, delimiter=',')
    # 跳过 CSV 文件的标题行
    next(reader)

    # 遍历 CSV 文件的每一行
    for row in reader:
        # 从行中提取时间戳（纳秒）
        timestamp_ns = int(row[0])
        # 将时间戳从纳秒转换为秒
        timestamp_s = timestamp_ns / 1e9
        # 提取位置信息
        px = row[1]
        py = row[2]
        pz = row[3]
        # 提取四元数信息，并调整顺序为 qx, qy, qz, qw
        qw = row[4]
        qx = row[5]
        qy = row[6]
        qz = row[7]

        # 按照 TUM 格式将数据写入 TXT 文件
        txtfile.write(f"{timestamp_s} {px} {py} {pz} {qx} {qy} {qz} {qw}\n")
    