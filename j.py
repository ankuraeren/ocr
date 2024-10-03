if input_method == "Upload Image File":
    uploaded_files = st.file_uploader(
        "Choose image(s) or PDF file(s)...",
        type=["jpg", "jpeg", "png", "bmp", "gif", "tiff", "pdf"],
        accept_multiple_files=True
    )
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            try:
                if file_extension == ".pdf":
                    # Convert PDF to images
                    with tempfile.TemporaryDirectory() as temp_dir:
                        pdf_path = os.path.join(temp_dir, uploaded_file.name)
                        with open(pdf_path, "wb") as f:
                            f.write(uploaded_file.read())
                        pages = convert_from_path(pdf_path)
                        for i, page in enumerate(pages):
                            page_filename = f"{os.path.splitext(uploaded_file.name)[0]}_page_{i+1}.jpg"
                            page_path = os.path.join(temp_dir, page_filename)
                            page.save(page_path, 'JPEG')
                            images.append(page)
                            image_paths.append(page_path)
                            pdf_pages.append(page)
                            st.image(page, caption=page_filename, use_column_width=True)
                else:
                    image = Image.open(uploaded_file)
                    images.append(image)
                    st.image(image, caption=uploaded_file.name, use_column_width=True)
                    temp_dir = tempfile.mkdtemp()
                    temp_dirs.append(temp_dir)
                    image_path = os.path.join(temp_dir, uploaded_file.name)
                    image.save(image_path)
                    image_paths.append(image_path)
            except Exception as e:
                st.error(f"Error processing file {uploaded_file.name}: {e}")
                logging.error(f"Error processing file {uploaded_file.name}: {e}")
