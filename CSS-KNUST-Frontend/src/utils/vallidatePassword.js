export function validatePassword(password) {
    const minLength = 8;
    const hasNumber = /\d/; 
    const hasLowercase = /[a-z]/;
    const hasUppercase = /[A-Z]/;
    const hasSymbol = /[!@#$%^&*(),.?":{}|<>]/;
  
    if (password.length < minLength) {
      return "Password must be at least 8 characters long.";
    }
    if (!hasNumber.test(password)) {
      return "Password must contain at least one number.";
    }
    if (!hasLowercase.test(password)) {
      return "Password must contain at least one lowercase letter.";
    }
    if (!hasUppercase.test(password)) {
      return "Password must contain at least one uppercase letter.";
    }
    if (!hasSymbol.test(password)) {
      return "Password must contain at least one symbol.";
    }
  
    return "Password is valid";
  }
  