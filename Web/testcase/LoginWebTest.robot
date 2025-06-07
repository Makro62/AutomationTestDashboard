*** Settings ***
Library         ../keywords/LoginKeywords.py

*** Variables ***
${VALID_USER}    standard_user
${VALID_PASS}    secret_sauce
${INVALID_USER}  invalid_user
${INVALID_PASS}  wrong_password

*** Test Cases ***

Valid Web Login Should Redirect To Inventory Page
    [Documentation]    Test login dengan akun valid
    Open Browser
    Login With Credentials    ${VALID_USER}    ${VALID_PASS}
    Verify Login Success
    Close Browser

Invalid Web Login Should Show Error Message
    [Documentation]    Test login dengan akun invalid
    Open Browser
    Login With Credentials    ${INVALID_USER}    ${INVALID_PASS}
    Verify Login Failed
    Close Browser
