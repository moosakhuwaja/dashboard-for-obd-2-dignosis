// When the page loads, execute the following code
window.onload = function () {
  // Get the login form element
  var loginForm = document.getElementById("login-form");

  // Add an event listener to the login form
  loginForm.addEventListener("submit", function (event) {
    // Prevent the default form submission behavior
    event.preventDefault();

    // Get the username and password inputs
    var usernameInput = document.getElementById("username-input");
    var passwordInput = document.getElementById("password-input");

    // Do some validation
    if (usernameInput.value === "") {
      alert("Please enter a username.");
      return;
    }
    if (passwordInput.value === "") {
      alert("Please enter a password.");
      return;
    }

    // If the validation passes, submit the form
    loginForm.submit();
  });
};
