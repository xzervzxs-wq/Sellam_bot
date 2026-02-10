#!/usr/bin/expect -f
set timeout 600

cd "/workspaces/Sellam_bot"

spawn bubblewrap build --skipPwaValidation

expect {
    "apply them to the project before building?" {
        send "yes\r"
        exp_continue
    }
    "versionName for the new App version:" {
        send "1.0.0\r"
        exp_continue
    }
    "Password for the Key Store:" {
        send "Quran@2024!\r"
        exp_continue
    }
    "Password for the Key:" {
        send "Quran@2024!\r"
        exp_continue
    }
    eof
}

wait
