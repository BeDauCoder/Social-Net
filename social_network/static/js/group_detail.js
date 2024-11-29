document.addEventListener("DOMContentLoaded", function () {
    // Get elements
    const deleteButton = document.getElementById("deleteGroupBtn");
    const updateButton = document.getElementById("updateGroupBtn");
    const shareButton = document.getElementById("shareGroupBtn");
    const joinGroupBtn = document.getElementById("joinGroupBtn");

    // Ensure CSRF token exists
    const csrfTokenInput = document.querySelector("input[name='csrfmiddlewaretoken']");
    if (!csrfTokenInput) {
        console.error("CSRF token is missing!");
        return;
    }
    const csrfToken = csrfTokenInput.value;

    // URLs passed from Django context
    const deleteUrl = typeof delete_group_url !== "undefined" ? delete_group_url : null;
    const updateUrl = typeof update_group_url !== "undefined" ? update_group_url : null;
    const redirectUrl = typeof list_group_url !== "undefined" ? list_group_url : null;

    // Delete Group
    if (deleteButton && deleteUrl && redirectUrl) {
        deleteButton.addEventListener("click", function () {
            if (confirm("Bạn có chắc chắn muốn xóa nhóm này không?")) {
                fetch(deleteUrl, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken,
                        "Content-Type": "application/json",
                    },
                })
                    .then((response) => {
                        if (response.ok) {
                            alert("Nhóm đã được xóa thành công.");
                            window.location.href = redirectUrl;
                        } else {
                            return response.json().then((data) => {
                                alert(data.error || "Đã xảy ra lỗi khi xóa nhóm.");
                            });
                        }
                    })
                    .catch((error) => console.error("Lỗi:", error));
            }
        });
    }

    // Update Group
    if (updateButton && updateUrl) {
        updateButton.addEventListener("click", function () {
            window.location.href = updateUrl;
        });
    }

    // Share Group
    if (shareButton) {
        shareButton.addEventListener("click", function () {
            const groupUrl = window.location.href; // Current page URL
            navigator.clipboard
                .writeText(groupUrl)
                .then(() => alert("Liên kết nhóm đã được sao chép vào clipboard."))
                .catch((error) => console.error("Lỗi sao chép văn bản:", error));
        });
    }

    // Join/Cancel Group Request
    if (joinGroupBtn) {
        joinGroupBtn.addEventListener("click", function () {
            const groupId = joinGroupBtn.dataset.groupId;
            if (!groupId) {
                console.error("Group ID is missing!");
                return;
            }

            const isCancelRequest = joinGroupBtn.textContent.trim() === "Hủy yêu cầu";
            const url = isCancelRequest
                ? `/groups/${groupId}/cancel-request/`
                : `/groups/${groupId}/join/`;

            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "Content-Type": "application/json",
                },
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.error) {
                        alert(data.error);
                        return;
                    }
                    alert(data.message);

                    // Update button state
                    if (isCancelRequest) {
                        joinGroupBtn.textContent = "Tham gia nhóm";
                        joinGroupBtn.classList.remove("btn-danger");
                        joinGroupBtn.classList.add("btn-primary");
                    } else {
                        joinGroupBtn.textContent = "Hủy yêu cầu";
                        joinGroupBtn.classList.remove("btn-primary");
                        joinGroupBtn.classList.add("btn-danger");
                    }
                })
                .catch((error) => console.error("Lỗi:", error));
        });
    }
});
