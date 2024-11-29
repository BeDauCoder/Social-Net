console.log("popup_form_add_group.js loaded successfully");

$('#postPageForm').on('submit', function (e) {
    e.preventDefault();
    var formData = new FormData(this);  // Use FormData for file uploads

    $.ajax({
        url: "{% url 'create_post_page' %}",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        success: function (response) {
            if (response.success) {
                $('#postPageModal').modal('hide');  // Close the modal
                $('#postPageForm')[0].reset();  // Clear the form

                // Display the new post (append to the post list or reload as needed)
                $('#postList').prepend(
                    `<div class="post">
                            <p>${response.content}</p>
                            <small>Được tạo vào: ${response.created_at}</small>
                        </div>`
                );
            } else {
                alert("Không thể tạo bài viết: " + JSON.stringify(response.errors));
            }
        }
    });
});
