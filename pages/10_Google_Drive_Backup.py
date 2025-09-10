import streamlit as st
import os
import json
from datetime import datetime
from utils.auth import require_admin, get_current_user
from utils.google_drive_backup import (
    GoogleDriveManager, 
    is_google_drive_configured,
    get_google_drive_config_status,
    setup_google_drive_instructions,
    create_full_backup,
    backup_surveys_to_drive,
    backup_responses_to_drive,
    backup_users_to_drive
)

st.set_page_config(
    page_title="Google Drive Backup - Khảo sát Hưng Yên",
    page_icon="☁️",
    layout="wide",
)

# Require admin authentication
require_admin()

st.title("☁️ Google Drive Backup")
st.markdown("Sao lưu dữ liệu khảo sát lên Google Drive")

# Check Google Drive configuration status
config_status = get_google_drive_config_status()
is_configured = config_status["configured"]

if not is_configured:
    # Setup instructions for secure configuration
    st.warning("⚠️ Google Drive chưa được cấu hình an toàn")
    
    with st.expander("📋 Hướng dẫn thiết lập Google Drive an toàn", expanded=True):
        st.markdown(setup_google_drive_instructions())
    
    st.error("🔒 **Lưu ý bảo mật:** Không sử dụng upload file credentials trực tiếp!")
    st.info("💡 **Khuyến nghị:** Sử dụng environment variables để bảo mật credentials")
    
    if st.button("🔄 Kiểm tra lại cấu hình"):
        st.rerun()

else:
    # Display configuration status
    st.success("✅ Google Drive đã được cấu hình")
    
    # Show detailed status
    with st.expander("📊 Thông tin cấu hình", expanded=False):
        st.write(f"**Phương pháp:** {config_status['method']}")
        
        for recommendation in config_status['recommendations']:
            if recommendation.startswith('✅'):
                st.success(recommendation)
            elif recommendation.startswith('⚠️'):
                st.warning(recommendation)
            elif recommendation.startswith('💡') or recommendation.startswith('🔧'):
                st.info(recommendation)
            else:
                st.write(recommendation)
    
    # Initialize Google Drive Manager
    if 'drive_manager' not in st.session_state:
        st.session_state.drive_manager = GoogleDriveManager()
    
    drive_manager = st.session_state.drive_manager
    
    # Authentication status
    if not hasattr(drive_manager, 'service') or drive_manager.service is None:
        with st.spinner("Đang xác thực với Google Drive..."):
            try:
                auth_success = drive_manager.authenticate()
            except Exception as e:
                auth_success = False
                st.error(f"❌ Lỗi xác thực: {str(e)}")
        
        if auth_success:
            st.success("✅ Xác thực Google Drive thành công!")
        else:
            st.error("❌ Xác thực Google Drive thất bại")
            
            with st.expander("💡 Hướng dẫn khắc phục", expanded=True):
                st.markdown("""
                **Các bước khắc phục:**
                
                1. **Kiểm tra file credentials:**
                   - Đảm bảo file `google_credentials.json` có định dạng chính xác
                   - Kiểm tra quyền truy cập Google Drive API đã được kích hoạt
                
                2. **Reset xác thực:**
                   - Xóa file `google_token.pickle` để xác thực lại
                   - Thực hiện lại quá trình xác thực
                
                3. **Trong môi trường headless:**
                   - Hệ thống sẽ hiển thị URL để xác thực
                   - Truy cập URL, đăng nhập và copy mã xác thực
                   - Dán mã xác thực vào ô nhập liệu
                """)
            
            if st.button("🔄 Thử lại xác thực"):
                st.rerun()
            
            st.stop()
    
    # Main backup interface
    st.header("📊 Sao lưu dữ liệu")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔄 Backup nhanh")
        
        if st.button("💾 Backup toàn bộ", use_container_width=True):
            with st.spinner("Đang sao lưu toàn bộ dữ liệu..."):
                try:
                    results = create_full_backup(drive_manager)
                    
                    success_count = sum(1 for r in results.values() if r is not None)
                    total_count = len(results)
                    
                    if success_count == total_count:
                        st.success(f"✅ Backup hoàn tất! Đã sao lưu {success_count}/{total_count} thành phần")
                    elif success_count > 0:
                        st.warning(f"⚠️ Backup một phần thành công: {success_count}/{total_count} thành phần")
                    else:
                        st.error("❌ Backup thất bại hoàn toàn")
                    
                    for component, file_id in results.items():
                        if file_id:
                            st.info(f"✅ {component.title()}: {file_id}")
                        else:
                            st.error(f"❌ {component.title()}: Thất bại")
                            
                except Exception as e:
                    st.error(f"❌ Lỗi backup: {str(e)}")
        
        if st.button("📋 Backup khảo sát", use_container_width=True):
            with st.spinner("Đang sao lưu khảo sát..."):
                try:
                    file_id = backup_surveys_to_drive(drive_manager)
                    if file_id:
                        st.success(f"✅ Backup khảo sát thành công! File ID: {file_id}")
                    else:
                        st.error("❌ Backup khảo sát thất bại")
                except Exception as e:
                    st.error(f"❌ Lỗi backup khảo sát: {str(e)}")
        
        if st.button("💬 Backup phản hồi", use_container_width=True):
            with st.spinner("Đang sao lưu phản hồi..."):
                try:
                    file_id = backup_responses_to_drive(drive_manager)
                    if file_id:
                        st.success(f"✅ Backup phản hồi thành công! File ID: {file_id}")
                    else:
                        st.error("❌ Backup phản hồi thất bại")
                except Exception as e:
                    st.error(f"❌ Lỗi backup phản hồi: {str(e)}")
        
        if st.button("👥 Backup người dùng", use_container_width=True):
            with st.spinner("Đang sao lưu người dùng..."):
                try:
                    file_id = backup_users_to_drive(drive_manager)
                    if file_id:
                        st.success(f"✅ Backup người dùng thành công! File ID: {file_id}")
                    else:
                        st.error("❌ Backup người dùng thất bại")
                except Exception as e:
                    st.error(f"❌ Lỗi backup người dùng: {str(e)}")
    
    with col2:
        st.subheader("📅 Backup tự động")
        
        st.info("""
        **Tính năng sắp ra mắt:**
        - Backup tự động hàng ngày
        - Backup khi có thay đổi dữ liệu
        - Thông báo email khi backup
        - Lọc backup theo thời gian
        """)
        
        # Backup schedule (placeholder)
        enable_auto = st.checkbox("🔄 Kích hoạt backup tự động", disabled=True)
        backup_time = st.time_input("⏰ Thời gian backup hàng ngày", disabled=True)
        backup_frequency = st.selectbox(
            "📆 Tần suất backup",
            ["Hàng ngày", "Hàng tuần", "Hàng tháng"],
            disabled=True
        )
    
    # Files management
    st.header("📁 Quản lý file backup")
    
    if st.button("🔄 Tải danh sách file"):
        with st.spinner("Đang tải danh sách file từ Google Drive..."):
            backup_files = drive_manager.list_backup_files(limit=50)
            st.session_state.backup_files = backup_files
    
    if 'backup_files' in st.session_state and st.session_state.backup_files:
        files = st.session_state.backup_files
        
        st.subheader(f"📂 {len(files)} file backup trên Google Drive")
        
        # Create DataFrame for display
        import pandas as pd
        
        file_data = []
        for file in files:
            # Parse file size
            size_mb = int(file.get('size', 0)) / (1024 * 1024) if file.get('size') else 0
            
            # Parse creation time
            created = file.get('createdTime', '')
            if created:
                try:
                    created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    created = created_dt.strftime('%d/%m/%Y %H:%M')
                except:
                    created = created[:10]
            
            file_data.append({
                'Tên file': file.get('name', 'N/A'),
                'Kích thước (MB)': f"{size_mb:.2f}",
                'Ngày tạo': created,
                'Mô tả': file.get('description', '')[:50] + ('...' if len(file.get('description', '')) > 50 else ''),
                'ID': file.get('id', '')
            })
        
        df = pd.DataFrame(file_data)
        st.dataframe(df, use_container_width=True)
        
        # File actions
        st.subheader("🔧 Thao tác với file")
        
        # Create a mapping of display names to file info for better selection
        file_options = {}
        for f in files:
            display_name = f"{f['name']} ({f['id'][:8]}...)"
            file_options[display_name] = f
        
        selected_file_display = st.selectbox(
            "Chọn file để thao tác",
            options=list(file_options.keys()),
            format_func=lambda x: x.split(' (')[0]
        )
        
        if selected_file_display:
            # Get selected file info by ID (more reliable than name)
            selected_file_info = file_options[selected_file_display]
            
            if selected_file_info:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📥 Tải xuống", use_container_width=True):
                        file_id = selected_file_info['id']
                        file_name = selected_file_info['name']
                        
                        with st.spinner(f"Đang tải {file_name}..."):
                            try:
                                success = drive_manager.download_file(file_id, f"/tmp/{file_name}")
                                
                                if success:
                                    # Get proper MIME type for the file
                                    mime_type = drive_manager.get_file_mime_type(file_name)
                                    
                                    # Provide download link with correct MIME type
                                    with open(f"/tmp/{file_name}", "rb") as file:
                                        st.download_button(
                                            label=f"💾 Tải {file_name}",
                                            data=file.read(),
                                            file_name=file_name,
                                            mime=mime_type
                                        )
                                    st.success("✅ File đã sẵn sàng tải xuống!")
                                    
                                    # Clean up temporary file
                                    try:
                                        os.remove(f"/tmp/{file_name}")
                                    except:
                                        pass  # Ignore cleanup errors
                                else:
                                    st.error("❌ Không thể tải file")
                            except Exception as e:
                                st.error(f"❌ Lỗi tải file: {str(e)}")
                
                with col2:
                    if st.button("🔗 Tạo link chia sẻ", use_container_width=True):
                        file_id = selected_file_info['id']
                        share_link = f"https://drive.google.com/file/d/{file_id}/view"
                        st.code(share_link)
                        st.info("📋 Copy link trên để chia sẻ file")
                
                with col3:
                    # Store deletion confirmation in session state
                    delete_key = f"confirm_delete_{selected_file_info['id']}"
                    
                    if st.button("🗑️ Xóa file", use_container_width=True, type="secondary"):
                        st.session_state[delete_key] = True
                    
                    # Show confirmation if button was clicked
                    if st.session_state.get(delete_key, False):
                        file_name = selected_file_info['name']
                        st.warning(f"⚠️ Bạn có chắc muốn xóa file '{file_name}'?")
                        
                        col_confirm1, col_confirm2 = st.columns(2)
                        
                        with col_confirm1:
                            if st.button("✅ Xác nhận", key=f"confirm_{selected_file_info['id']}", type="primary"):
                                with st.spinner("Đang xóa file..."):
                                    try:
                                        success = drive_manager.delete_file(selected_file_info['id'])
                                        
                                        if success:
                                            st.success("✅ Đã xóa file thành công")
                                            # Clear confirmation state
                                            del st.session_state[delete_key]
                                            # Refresh file list
                                            backup_files = drive_manager.list_backup_files(limit=50)
                                            st.session_state.backup_files = backup_files
                                            st.rerun()
                                        else:
                                            st.error("❌ Không thể xóa file")
                                    except Exception as e:
                                        st.error(f"❌ Lỗi xóa file: {str(e)}")
                        
                        with col_confirm2:
                            if st.button("❌ Hủy", key=f"cancel_{selected_file_info['id']}"):
                                # Clear confirmation state
                                del st.session_state[delete_key]
                                st.rerun()
    
    # Settings
    st.header("⚙️ Cài đặt")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Cấu hình Google Drive")
        
        if st.button("🔄 Reset xác thực", use_container_width=True):
            # Remove token file to force re-authentication
            if os.path.exists('google_token.pickle'):
                os.remove('google_token.pickle')
                st.success("✅ Đã reset xác thực. Sẽ yêu cầu đăng nhập lại lần sau.")
        
        if st.button("📁 Mở thư mục backup", use_container_width=True):
            # Open Google Drive folder
            if hasattr(drive_manager, 'survey_folder_id') and drive_manager.survey_folder_id:
                folder_url = f"https://drive.google.com/drive/folders/{drive_manager.survey_folder_id}"
                st.markdown(f"[🔗 Mở thư mục backup]({folder_url})")
            else:
                st.info("Chưa tạo thư mục backup. Thực hiện backup để tạo thư mục.")
    
    with col2:
        st.subheader("📊 Thống kê backup")
        
        if 'backup_files' in st.session_state:
            files = st.session_state.backup_files
            
            total_size = sum(int(f.get('size', 0)) for f in files) / (1024 * 1024)  # MB
            
            st.metric("Tổng số file", len(files))
            st.metric("Tổng dung lượng", f"{total_size:.2f} MB")
            
            # File types
            file_types = {}
            for file in files:
                name = file.get('name', '')
                if 'survey' in name.lower():
                    file_types['Khảo sát'] = file_types.get('Khảo sát', 0) + 1
                elif 'response' in name.lower():
                    file_types['Phản hồi'] = file_types.get('Phản hồi', 0) + 1
                elif 'user' in name.lower():
                    file_types['Người dùng'] = file_types.get('Người dùng', 0) + 1
                else:
                    file_types['Khác'] = file_types.get('Khác', 0) + 1
            
            st.write("**Phân loại file:**")
            for file_type, count in file_types.items():
                st.write(f"• {file_type}: {count} file")

# Quick navigation
st.markdown("---")
st.subheader("🚀 Thao tác nhanh")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🏠 Về trang chủ", use_container_width=True):
        st.switch_page("app.py")

with col2:
    if st.button("⚙️ Panel admin", use_container_width=True):
        st.switch_page("pages/8_Admin.py")

with col3:
    if st.button("📈 Dashboard", use_container_width=True):
        st.switch_page("pages/9_Dashboard_Admin.py")

with col4:
    if st.button("📊 Phân tích dữ liệu", use_container_width=True):
        st.switch_page("pages/4_Data_Analysis.py")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p><strong>Google Drive Backup System</strong></p>
        <p>Sao lưu an toàn dữ liệu khảo sát lên cloud</p>
    </div>
    """, 
    unsafe_allow_html=True
)