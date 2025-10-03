# coding=utf-8
#!/usr/bin/env python3
import os
import sys
import struct
from pathlib import Path

PART_SIZES = [64, 1024, 1024, 1024, 1024, 1024, 1024, 1024, 56320, 860160]
TOTAL_SIZE = sum(PART_SIZES)  # 应为932712

def validate_file_sizes(file_paths):
    """验证文件大小是否符合预期"""
    for i, path in enumerate(file_paths):
        actual_size = os.path.getsize(path)
        if actual_size != PART_SIZES[i]:
            print(f"错误: 文件{path}大小应为{PART_SIZES[i]}字节，实际为{actual_size}字节")
            return False
    return True

def unpack_sp_file(input_dir):
    """拆分original.sp文件为10个部分"""
    input_path = os.path.join(input_dir, "original.sp")
    if not os.path.exists(input_path):
        print(f"错误: 未找到输入文件 {input_path}")
        sys.exit(1)
    
    if os.path.getsize(input_path) != TOTAL_SIZE:
        print(f"错误: original.sp文件大小应为{TOTAL_SIZE}字节")
        sys.exit(1)
    
    try:
        with open(input_path, "rb") as f_in:
            for i, size in enumerate(PART_SIZES):
                part_path = os.path.join(input_dir, f"part{i}")
                with open(part_path, "wb") as f_out:
                    f_out.write(f_in.read(size))
        print(f"成功拆分文件到{input_dir}目录")
    except Exception as e:
        print(f"拆分文件时出错: {str(e)}")
        sys.exit(1)

def repack_sp_file(output_dir):
    """合并10个部分为new.sp文件"""
    part_files = [os.path.join(output_dir, f"part{i}") for i in range(10)]
    
    # 检查所有部分文件是否存在
    for path in part_files:
        if not os.path.exists(path):
            print(f"错误: 未找到文件 {path}")
            sys.exit(1)
    
    # 验证文件大小
    if not validate_file_sizes(part_files):
        sys.exit(1)
    
    try:
        output_path = os.path.join(output_dir, "new.sp")
        with open(output_path, "wb") as f_out:
            for path in part_files:
                with open(path, "rb") as f_in:
                    f_out.write(f_in.read())
        print(f"成功合并文件到 {output_path}")
    except Exception as e:
        print(f"合并文件时出错: {str(e)}")
        sys.exit(1)

def unpack_file(input_file, output_folder):
    with open(input_file, 'rb') as f:
        # 读取头部类型并验证
        try:
            header_type = f.read(1)[0]
            if header_type not in (0x00, 0x01):
                print(f"Error: Invalid header type {hex(header_type)} (expected 0x00 or 0x01)")
                sys.exit(1)
        except IndexError:
            print("Error: Failed to read header type (file may be empty or corrupted)")
            sys.exit(1)
        
        # 读取文件数量并验证
        try:
            file_count = struct.unpack('>I', f.read(4))[0]
            if file_count == 0:
                print("Error: File count is 0 (invalid package)")
                sys.exit(1)
        except struct.error:
            print("Error: Failed to read file count (file may be corrupted)")
            sys.exit(1)
        
        # 读取文件大小列表并验证
        file_sizes = []
        try:
            for _ in range(file_count):
                size = struct.unpack('>I', f.read(4))[0]
                if size == 0:
                    print("Error: Found file with size 0 (invalid package)")
                    sys.exit(1)
                file_sizes.append(size)
        except struct.error:
            print("Error: Failed to read file sizes (file may be corrupted)")
            sys.exit(1)
        
        # 读取文件名（如果是type1）
        filenames = []
        if header_type == 0x01:
            try:
                for _ in range(file_count):
                    name_len = struct.unpack('>H', f.read(2))[0]
                    filenames.append(f.read(name_len).decode('ascii'))
            except (struct.error, UnicodeDecodeError) as e:
                print(f"Error: Failed to read filenames - {str(e)}")
                sys.exit(1)
        
        # 创建输出目录
        file_size_m = os.path.getsize(input_file)
        size_dir = f"size_{file_size_m}"
        type_dir = "type0" if header_type == 0x00 else "type1"
        
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
        (output_path / size_dir).mkdir(exist_ok=True)
        (output_path / type_dir).mkdir(exist_ok=True)
        
        print(f"Unpacking {file_count} files from {input_file}...")
        print(f"Header type: {'type1 (with filenames)' if header_type == 0x01 else 'type0 (no filenames)'}")
        
        # 提取文件数据
        for i in range(file_count):
            if header_type == 0x00:
                # 生成补零的数字文件名
                filename = f"{i:0{len(str(file_count))}d}"
            else:
                # 添加序号前缀
                prefix = f"#{i:0{len(str(file_count))}d}#-"
                filename = prefix + filenames[i]
            
            file_path = output_path / filename
            try:
                with open(file_path, 'wb') as out_file:
                    out_file.write(f.read(file_sizes[i]))
            except IOError as e:
                print(f"Error: Failed to write file {filename} - {str(e)}")
                sys.exit(1)
            
            print(f"Extracted: {filename} ({file_sizes[i]} bytes)")
        
        print(f"Unpack completed to {output_folder}")

def repack_files(input_folder, output_file):
    input_path = Path(input_folder)
    
    # 确定打包类型
    if (input_path / "type0").exists():
        header_type = 0x00
        print("Packing as type0 (no filenames)")
    elif (input_path / "type1").exists():
        header_type = 0x01
        print("Packing as type1 (with filenames)")
    else:
        print("Error: Could not determine package type (missing type0 or type1 directory)")
        sys.exit(1)
    
    # 获取文件列表（保留原始文件名）
    if header_type == 0x00:
        # 按数字顺序排序
        files = sorted(
            [f for f in input_path.iterdir() if f.is_file() and not f.name.startswith('type') and not f.name.startswith('size')],
            key=lambda x: int(x.name)
        )
    else:
        # 按文件名排序（保留原始文件名）
        files = sorted(
            [f for f in input_path.iterdir() if f.is_file() and not f.name.startswith('type') and not f.name.startswith('size')],
            key=lambda x: x.name
        )
    
    file_count = len(files)
    if file_count == 0:
        print("Error: No files found to pack")
        sys.exit(1)
    
    print(f"Packing {file_count} files to {output_file}...")
    
    # 准备头部数据
    header = bytes([header_type])
    header += struct.pack('>I', file_count)
    
    file_sizes = []
    for file in files:
        # 使用原始文件名获取文件大小
        file_size = file.stat().st_size
        file_sizes.append(file_size)
        header += struct.pack('>I', file_size)
    
    if header_type == 0x01:
        for file in files:
            # 使用去除前缀的文件名写入头部
            clean_name = get_original_name(file.name)
            filename = clean_name.encode('ascii')
            header += struct.pack('>H', len(filename))
            header += filename
    
    # 准备文件数据（使用原始文件名读取）
    file_data = b''
    for file in files:
        with open(file, 'rb') as f:
            file_data += f.read()
    
    # 写入输出文件
    with open(output_file, 'wb') as f:
        f.write(header)
        f.write(file_data)
    
    # 检查是否需要填充冗余数据
    size_dirs = [d for d in input_path.iterdir() if d.is_dir() and d.name.startswith('size_')]
    if size_dirs:
        target_size = int(size_dirs[0].name[5:])
        current_size = os.path.getsize(output_file)
        
        if current_size < target_size:
            padding = target_size - current_size
            print(f"Adding {padding} bytes of padding to match target size {target_size}")
            with open(output_file, 'ab') as f:
                f.write(b'\x00' * padding)
    
    print(f"Pack completed to {output_file}")

def get_original_name(filename):
    """获取去除前缀的文件名"""
    if filename.startswith('#') and '#' in filename[1:]:
        prefix_end = filename.find('#', 1) + 1
        return filename[prefix_end+1:]  # 跳过"-"符号
    return filename

def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Unpack: tsspack.py unpacksp input_folder")
        print("  Repack: tsspack.py repacksp input_folder")
        print("  Unpack: tsspack.py unpack input_file output_folder")
        print("  Repack: tsspack.py repack input_folder output_file")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'unpacksp':
        input_folder = sys.argv[2]
        unpack_sp_file(input_folder)
    elif command == 'repacksp':
        input_folder = sys.argv[2]
        repack_sp_file(input_folder)
    elif command == 'unpack':
        input_file = sys.argv[2]
        output_folder = sys.argv[3]
        unpack_file(input_file, output_folder)
    elif command == 'repack':
        input_folder = sys.argv[2]
        output_file = sys.argv[3]
        repack_files(input_folder, output_file)
    else:
        print(f"Error: Unknown command '{command}'")
        sys.exit(1)

if __name__ == '__main__':
    main()
