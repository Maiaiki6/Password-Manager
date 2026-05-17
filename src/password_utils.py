"""
Password generation and strength evaluation utilities.
"""

import random
import string


class PasswordUtils:
    """Utilities for password generation and strength evaluation."""
    
    # Character sets for password generation
    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    DIGITS = string.digits
    SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    @staticmethod
    def generate_strong_password(length=16, use_symbols=True):
        """
        Generate a random strong password.
        
        Args:
            length (int): Password length (default 16)
            use_symbols (bool): Include special characters (default True)
            
        Returns:
            str: Generated password
        """
        if length < 8:
            length = 8
        
        # Build character pool
        char_pool = PasswordUtils.LOWERCASE + PasswordUtils.UPPERCASE + PasswordUtils.DIGITS
        if use_symbols:
            char_pool += PasswordUtils.SYMBOLS
        
        # Ensure at least one char from each required set
        required_chars = [
            random.choice(PasswordUtils.LOWERCASE),
            random.choice(PasswordUtils.UPPERCASE),
            random.choice(PasswordUtils.DIGITS)
        ]
        
        if use_symbols:
            required_chars.append(random.choice(PasswordUtils.SYMBOLS))
        
        # Fill remaining length with random chars from pool
        remaining_length = length - len(required_chars)
        password_chars = required_chars + [random.choice(char_pool) for _ in range(remaining_length)]
        
        # Shuffle to avoid predictable pattern
        random.shuffle(password_chars)
        
        return ''.join(password_chars)
    
    @staticmethod
    def check_strength(password):
        """
        Evaluate password strength.
        
        Args:
            password (str): Password to evaluate
            
        Returns:
            dict: {
                'score': int (0-5),
                'strength': str ('Very Weak', 'Weak', 'Fair', 'Good', 'Strong', 'Very Strong'),
                'feedback': list of str (suggestions for improvement),
                'meets_minimum': bool (True if score >= 2)
            }
        """
        score = 0
        feedback = []
        
        # Length checks
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Password should be at least 8 characters")
        
        if len(password) >= 12:
            score += 1
        else:
            feedback.append("Consider using at least 12 characters")
        
        # Character variety checks
        has_lower = any(c in PasswordUtils.LOWERCASE for c in password)
        has_upper = any(c in PasswordUtils.UPPERCASE for c in password)
        has_digit = any(c in PasswordUtils.DIGITS for c in password)
        has_symbol = any(c in PasswordUtils.SYMBOLS for c in password)
        
        variety_count = sum([has_lower, has_upper, has_digit, has_symbol])
        
        if variety_count >= 3:
            score += 2
        elif variety_count >= 2:
            score += 1
        else:
            feedback.append("Use a mix of uppercase, lowercase, numbers, and symbols")
        
        if has_symbol:
            score += 1
        else:
            feedback.append("Add special characters like !@#$%^&*()")
        
        # Map score to strength level
        strength_levels = [
            "Very Weak",
            "Weak",
            "Fair",
            "Good",
            "Strong",
            "Very Strong"
        ]
        
        strength = strength_levels[min(score, 5)]
        meets_minimum = score >= 2
        
        return {
            'score': score,
            'strength': strength,
            'feedback': feedback,
            'meets_minimum': meets_minimum
        }
    
    @staticmethod
    def validate_master_password(password):
        """
        Validate master password meets minimum requirements.
        Master password should be stronger than regular passwords.
        
        Args:
            password (str): Master password to validate
            
        Returns:
            tuple: (is_valid: bool, feedback: str or None)
        """
        if len(password) < 12:
            return False, "Master password must be at least 12 characters"
        
        has_lower = any(c in PasswordUtils.LOWERCASE for c in password)
        has_upper = any(c in PasswordUtils.UPPERCASE for c in password)
        has_digit = any(c in PasswordUtils.DIGITS for c in password)
        
        if not (has_lower and has_upper and has_digit):
            return False, "Master password must contain uppercase, lowercase, and numbers"
        
        return True, None
