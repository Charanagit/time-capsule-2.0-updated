document.addEventListener('DOMContentLoaded', function() {
    const customDateInput = document.getElementById('customDate');
    const customScheduleRadio = document.getElementById('customSchedule');
    const oneYearScheduleRadio = document.getElementById('oneYearSchedule');

    // Initially disable the custom date
    customDateInput.disabled = true;

    // Enable/Disable custom date based on selected radio button
    customScheduleRadio.addEventListener('change', function() {
        customDateInput.disabled = false;
    });

    oneYearScheduleRadio.addEventListener('change', function() {
        customDateInput.disabled = true;
    });
});
