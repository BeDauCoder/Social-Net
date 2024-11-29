function validateForm() {
    let isValid = true;

    // Kiểm tra trường 'name'
    const nameInput = document.getElementById("id_name");
    if (nameInput.value.trim() === "") {
        nameInput.classList.add("is-invalid");
        nameInput.classList.remove("is-valid");
        isValid = false;
    } else {
        nameInput.classList.remove("is-invalid");
        nameInput.classList.add("is-valid");
    }

    // Kiểm tra trường 'description'
    const descriptionInput = document.getElementById("id_description");
    if (descriptionInput.value.trim() === "") {
        descriptionInput.classList.add("is-invalid");
        descriptionInput.classList.remove("is-valid");
        isValid = false;
    } else {
        descriptionInput.classList.remove("is-invalid");
        descriptionInput.classList.add("is-valid");
    }

    return isValid; // Chỉ cho phép gửi form nếu tất cả các trường đều hợp lệ
}