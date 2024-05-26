

document.addEventListener('DOMContentLoaded', function() {
    // Your JavaScript code here
    $('input[name="level"]').on('change', function() {
        $('#start-btn').show();
    });

    const timerDisplay = document.getElementById('timer');
    let timeRemaining;

    function updateTimerDisplay() {
        const minutes = Math.floor(timeRemaining / 60);
        const seconds = timeRemaining % 60;
        timerDisplay.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    }

    function startTimer() {
        const timerInterval = setInterval(() => {
            timeRemaining--;
            updateTimerDisplay();
            if (timeRemaining <= 0) {
                clearInterval(timerInterval);
                submitQuiz();
            }
        }, 1000);
    }

    fetch('/quiz/get_remaining_time')
        .then(response => response.json())
        .then(data => {
            timeRemaining = data.remaining_time;
            updateTimerDisplay();
            startTimer();
        })
        .catch(error => console.error('Error fetching remaining time:', error));

    showQuestion(currentQuestion);
});





function startQuiz() {
    const selectedLevel = $('input[name="level"]:checked').val();
    console.log(selectedLevel);
    if (selectedLevel) {
        // send post request to start the quiz
        formdata = new FormData();
        formdata.append('level', selectedLevel);
        fetch('/quiz/start', {
            method: 'POST',
            body: formdata
        }).then(response => {
            // Check if the response is a redirect
            if (response.redirected) {
                // Redirect the user to the new location
                window.location.href = response.url;
            } else {
                // Handle other responses if needed
                console.log('Request was not redirected');
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
}

function submitQuiz() {
    const questions = document.querySelectorAll('.card');
    const selectedOptions = Array.from(questions).map((question, i) => {
        const selectedOption = question.querySelector(`input[name="answer-choice${i}"]:checked`);
        return selectedOption ? selectedOption.value : null;
    });
    console.log(selectedOptions);
    formdata = new FormData();
    selectedOptions.forEach((option, i) => {
        formdata.append('answers', option);
    });
    fetch('/quiz/submit', {
        method: 'POST',
        body: formdata
    }).then(response => {
        // Check if the response is a redirect
        if (response.redirected) {
            // Redirect the user to the new location
            window.location.href = response.url;
        } else {
            // Handle other responses if needed
            console.log('Request was not redirected');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}



