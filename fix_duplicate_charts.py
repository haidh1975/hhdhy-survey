import re

# Đọc nội dung file
file_path = 'pages/4_Data_Analysis.py'
with open(file_path, 'r') as file:
    content = file.read()

# Tìm và thay thế tất cả các lệnh st.plotly_chart
# Mẫu regex để tìm các lệnh st.plotly_chart
pattern = r'(st\.plotly_chart\(fig,\s*use_container_width=True\))'

# Đọc lại nội dung theo từng dòng để thêm key
lines = content.split('\n')
new_lines = []
chart_counter = 0

for line in lines:
    if 'st.plotly_chart(fig, use_container_width=True)' in line:
        # Thêm key duy nhất
        chart_counter += 1
        indentation = len(line) - len(line.lstrip())
        new_line = line[:indentation] + f'st.plotly_chart(fig, use_container_width=True, key="chart_{chart_counter}")'
        new_lines.append(new_line)
    else:
        new_lines.append(line)

# Ghi nội dung mới vào file
with open(file_path, 'w') as file:
    file.write('\n'.join(new_lines))

print(f"Đã cập nhật {chart_counter} biểu đồ plotly_chart với các key duy nhất.")