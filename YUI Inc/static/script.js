document.addEventListener("DOMContentLoaded", function() {
    const enrollButtons = document.querySelectorAll('.btn-primary');

    enrollButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent the default form submission
            const confirmation = confirm("Are you sure you want to enroll in this course?");
            if (confirmation) {
                this.closest('form').submit(); // Submit the form if confirmed
            }
        });
    });
});
