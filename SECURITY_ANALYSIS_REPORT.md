# Security Compliance Analysis: RoyalPark Project vs Yelo Bank Contract

## Overview
This analysis compares the security requirements from the Yelo Bank payment contract (№1, dated 11.03.2026) with the RoyalPark project implementation to identify gaps and potential security risks.

---

## 1. CRITICAL SECURITY ISSUES FOUND

### 1.1 Hardcoded Credentials in config.py
**Location:** `/Application/Backend/app/config.py`

**Issue:**
```python
PG_PASSWORD: str = os.getenv("PG_PASSWORD", "admin Ayaz")
ROOT_PASSWORD: str = os.getenv("ROOT_PASSWORD", "admin Ayaz")
SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "change-this-in-production")
```

**Risk Level:** RED CRITICAL

**Contract Violation:**
- Section 3.2.10: Təsərrüfat subyekti must ensure security of information resources against internal and external threats
- PCI DSS requirements for secure configuration

**Recommendation:**
- NEVER use hardcoded passwords in code
- Use environment variables only (no defaults for passwords)
- Use strong, randomly generated passwords

---

### 1.2 Missing HTTPS Configuration
**Location:** `/Application/Backend/app/security.py:26`

**Issue:**
```python
secure=False,  # must be True for HTTPS in production
```

**Risk Level:** RED CRITICAL

**Contract Violation:**
- Section: "Müasir protokollardan və 3DSecure texnologiyasından istifadə etməklə... təhlükəsiz aparılmasını təmin etmək"
- PCI DSS Requirement 4: Encrypt transmission of cardholder data across open networks

**Recommendation:**
- Set `secure=True` for production (HTTPS only)
- Implement HTTPS at server/proxy level
- Use HSTS headers

---

### 1.3 BINTable API Key Exposed
**Location:** `/Application/Backend/app/routers/api_payment.py:13`

**Issue:**
```python
BINTABLE_API_KEY = "acb605ffc7f764ffb8bb7539d1ffdea48b22a7db"
```

**Risk Level:** ORANGE HIGH

**Recommendation:**
- Move to environment variable
- Rotate exposed API key immediately

---

### 1.4 Insecure CORS Configuration
**Location:** `/Application/Backend/app/main.py:226-239`

**Issue:** Wildcard CORS settings with `allow_methods=["*"]`, `allow_headers=["*"]`

**Risk Level:** YELLOW MEDIUM

**Recommendation:**
- Restrict to specific origins in production
- Don't use wildcard `*` for methods/headers

---

### 1.5 Public Endpoints Without Authentication
**Location:** Multiple endpoints with `/public` suffix

**Examples:**
- `/api/payments/public` - Create payment without auth
- `/api/payments/{payment_id}/open-invoices/public`
- `/api/payments/{payment_id}/auto-apply/public`
- `/api/payments/{payment_id}/applications/public`

**Risk Level:** RED CRITICAL

**Contract Violation:**
- Section: Cardholder data must be protected
- PCI DSS Requirement 7: Restrict access to cardholder data by business need to know

**Recommendation:**
- Remove public endpoints OR
- Add proper authentication + rate limiting + IP whitelisting
- These should NEVER be publicly accessible

---

## 2. PCI DSS COMPLIANCE ISSUES

### 2.1 Card Data Handling
**Contract Requirement:**
> "Saytda (elektron vitrində) Müştərinin sifarişinin rəsmiləşdirilməsi zamanı istifadə edilən səhifələrdə Müştərinin kartının rekvizitləri (PAN nömrəsi, CVC2/CVV2, kartın bitmə tarixi) tələb edilməməlidir."

**Status:** GOOD - Your project uses AzeriCard gateway, so card data is handled by the payment processor

**What to verify:**
- Ensure card data is NEVER stored in your database
- Ensure card data is NEVER logged
- Ensure card data is NEVER exposed in API responses

---

### 2.2 3D Secure Implementation
**Contract Requirement:**
> "Müasir protokollardan və 3DSecure texnologiyasından istifadə etməklə... təhlükəsiz aparılmasını təmin etmək"

**Status:** NEEDS VERIFICATION

**Contract References:**
- Section on 3D Secure: "Verified by Visa, MasterCard SecureCode"

**What to check:**
- Is 3D Secure enabled on AzeriCard gateway?
- The contract mentions specific terminals (3 terminals for API testing)
- Verify 3DS is configured in `AZERICARD_GATEWAY_URL`

---

### 2.3 Data Retention and Audit Logging
**Contract Requirement:**
> "Kartlardan istifadə edilməklə həyata keçirilən əməliyyatlar üzrə sənədləri... müvafiq əməliyyatın aparıldığı tarixdən saxlamaq"

**Status:** PARTIALLY IMPLEMENTED

**Your Implementation:**
- `PaymentLog` table exists
- Logs payment actions

**Gaps:**
- Need to verify retention period (contract requires documentation retention)
- Need audit trail for all payment-related operations
- Missing: Failed authentication attempts logging

---

## 3. DATA SECURITY GAPS

### 3.1 Password Storage
**Status:** GOOD

```python
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
```

**Analysis:** Argon2 is a strong password hashing algorithm. This is PCI DSS compliant.

---

### 3.2 Session Security
**Location:** `/Application/Backend/app/security.py`

**Current:**
- httponly=True (GOOD)
- samesite="lax" (should be "strict" for sensitive apps)
- secure=False (CRITICAL - must be True for HTTPS)
- max_age=8 hours (reasonable)

**Recommendations:**
- Change `samesite` to `"strict"` for better CSRF protection
- Set `secure=True` for production

---

## 4. CONTRACT-SPECIFIC REQUIREMENTS CHECKLIST

| Requirement | Status | Notes |
|------------|--------|-------|
| SSL/TLS encryption | NEEDS FIX | secure=False in config |
| 3D Secure support | VERIFY WITH BANK | Check with Yelo Bank |
| PCI DSS compliance | PARTIAL | Need certification |
| No card data storage | GOOD | Using gateway |
| Transaction logging | GOOD | PaymentLog table |
| Confidentiality of data | NEEDS NDA | Contract clause |
| Website security | NEEDS HARDENING | CORS, headers |
| Regular security audits | MISSING | Not implemented |

---

## 5. SPECIFIC RECOMMENDATIONS

### Immediate Actions (Before Going Live):

1. **Remove all hardcoded credentials**
```python
# config.py - Change to:
PG_PASSWORD: str = os.getenv("PG_PASSWORD")  # No default!
ROOT_PASSWORD: str = os.getenv("ROOT_PASSWORD")  # No default!
SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY")  # Must be set!
```

2. **Fix HTTPS configuration**
```python
# security.py
response.set_cookie(
    secure=True,  # NOT False
    samesite="strict",  # NOT "lax"
)
```

3. **Move API keys to environment variables**
```python
# api_payment.py
BINTABLE_API_KEY = os.getenv("BINTABLE_API_KEY")
```

4. **Secure public endpoints**
```python
# Add authentication to /public endpoints
# OR remove them entirely if not needed
```

5. **Add security headers middleware**

---

## 6. TERMINAL SPECIFIC NOTES

According to the contract, you're getting **3 terminals for API testing**. This means:

1. Each terminal should have its own `AZERICARD_TERMINAL_ID`
2. Test environment should be separate from production
3. Terminal credentials should be rotated regularly

---

## 7. SUMMARY

### Critical Issues to Fix Before Production:
- [ ] Remove hardcoded passwords from config.py
- [ ] Enable HTTPS (secure=True)
- [ ] Secure or remove public endpoints
- [ ] Move API keys to environment variables
- [ ] Configure proper CORS

### Important Improvements:
- [ ] Add rate limiting
- [ ] Implement IP whitelisting
- [ ] Add security headers
- [ ] Implement proper audit logging
- [ ] Add failed login attempt tracking

### Contract Compliance:
- The project has a good foundation with AzeriCard gateway integration
- Card data is NOT stored (compliant)
- Password hashing is secure (Argon2)
- Payment logging exists
- Main gaps are in configuration and HTTPS setup

---

## 8. NEXT STEPS

1. Fix all CRITICAL issues immediately
2. Schedule security audit before going live
3. Contact Yelo Bank for PCI DSS certification guidance
4. Set up monitoring and alerting for suspicious activities
5. Implement regular security scanning
