document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.js-dismiss-alert');

    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const url = this.dataset.dismissUrl;
            const alertId = this.dataset.alertId;
            // READ TOKEN FROM HTML
            const csrfToken = this.dataset.csrfToken;

            // Remove from UI immediately
            const alertBox = document.getElementById('site-alert-' + alertId);
            if (alertBox) alertBox.remove();

            // Send to server
            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                },
            }).catch(err => console.error('Error dismissing alert:', err));
        });
    });
});
