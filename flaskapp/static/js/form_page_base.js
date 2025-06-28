// Customer type toggle functionality
document.addEventListener('DOMContentLoaded', function () {
    // タイプ切り替え
    const typeOptions = document.querySelectorAll('.type-option');
    const typeSelect = document.getElementById('typeofcustomer');
    const individualSection = document.getElementById('individual-section');
    const corporateSection = document.getElementById('corporate-section');

    if (typeOptions && typeSelect && individualSection && corporateSection) {
        typeOptions.forEach(option => {
            option.addEventListener('click', () => {
                typeOptions.forEach(opt => opt.classList.remove('active'));
                option.classList.add('active');
                typeSelect.value = option.dataset.type;

                if (option.dataset.type === '個人') {
                    individualSection.classList.add('active');
                    corporateSection.classList.remove('active');
                } else {
                    individualSection.classList.remove('active');
                    corporateSection.classList.add('active');
                }
            });
        });
    }

    // 年齢自動計算
    const birthDateInput = document.getElementById('individual_birthDate');
    const ageInput = document.getElementById('individual_age');
    if (birthDateInput && ageInput) {
        birthDateInput.addEventListener('change', () => {
            let v = birthDateInput.value.replace(/[^\d]/g, '');
            if (v.length === 8) {
                const birthDate = new Date(
                    v.substr(0, 4) + '-' + v.substr(4, 2) + '-' + v.substr(6, 2)
                );
                const today = new Date();
                let age = today.getFullYear() - birthDate.getFullYear();
                const monthDiff = today.getMonth() - birthDate.getMonth();
                if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
                    age--;
                }
                ageInput.value = age >= 0 ? age : '';
            }
        });
    }

    // 和暦変換
    function toWareki(ymd) {
        let y, m, d;
        if (/^\d{8}$/.test(ymd)) {
            y = parseInt(ymd.substr(0, 4), 10);
            m = parseInt(ymd.substr(4, 2), 10);
            d = parseInt(ymd.substr(6, 2), 10);
        } else {
            return "";
        }
        const eras = [
            { name: "令和", start: [2019, 5, 1] },
            { name: "平成", start: [1989, 1, 8] },
            { name: "昭和", start: [1926, 12, 25] },
            { name: "大正", start: [1912, 7, 30] },
            { name: "明治", start: [1868, 1, 25] }
        ];
        for (let era of eras) {
            const [ey, em, ed] = era.start;
            if (
                y > ey ||
                (y === ey && m > em) ||
                (y === ey && m === em && d >= ed)
            ) {
                let nen = y - ey + 1;
                return `${era.name}${nen === 1 ? "元" : nen}年${m}月${d}日`;
            }
        }
        return "";
    }

    // 和暦表示（生年月日）
    const warekiSpan = document.getElementById('wareki_birthdate');
    if (birthDateInput && warekiSpan) {
        function updateWareki() {
            let v = birthDateInput.value.replace(/[^\d]/g, '');
            if (v.length === 8) {
                warekiSpan.textContent = toWareki(v);
            } else if (/^\d{4}\/\d{2}\/\d{2}$/.test(birthDateInput.value)) {
                warekiSpan.textContent = toWareki(birthDateInput.value);
            } else {
                warekiSpan.textContent = "";
            }
        }
        birthDateInput.addEventListener('input', updateWareki);
        birthDateInput.addEventListener('blur', updateWareki);
        updateWareki();
    }

    // 生年月日8桁入力時に西暦・和暦を表示（西暦は「2025年04月11日」形式）
    const seirekiSpan = document.getElementById('seireki_birthdate');
    if (birthDateInput && seirekiSpan && warekiSpan) {
        function updateBirthDateDisplay() {
            let v = birthDateInput.value.replace(/[^\d]/g, '');
            if (v.length === 8) {
                // 西暦表示（YYYY年MM月DD日）
                seirekiSpan.textContent = `${v.substr(0,4)}年${v.substr(4,2)}月${v.substr(6,2)}日`;
                // 和暦表示
                warekiSpan.textContent = toWareki(v);
            } else {
                seirekiSpan.textContent = "";
                warekiSpan.textContent = "";
            }
        }
        birthDateInput.addEventListener('input', updateBirthDateDisplay);
        birthDateInput.addEventListener('blur', updateBirthDateDisplay);
        updateBirthDateDisplay();
    }

    // フォームバリデーション
    const form = document.querySelector('.customer-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.style.borderColor = '#e74c3c';
                    isValid = false;
                } else {
                    field.style.borderColor = '#e1e8ed';
                }
            });
            if (!isValid) {
                e.preventDefault();
                alert('必須項目を入力してください。');
            }
        });

        // Enterキーによるフォームの自動送信を無効化
        form.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
            }
        });
    }

    // 電話番号入力の制御（手動でのハイフン入力を許可）
const phoneFields = document.querySelectorAll('input[name*="tel"]');
phoneFields.forEach(field => {
    field.addEventListener('input', (e) => {
        // 入力された値から「数字」と「ハイフン」以外の文字を削除する
        let value = e.target.value.replace(/[^\d-]/g, '');
        e.target.value = value;
    });
});

    // 郵便番号入力の制御（手動でのハイフン入力を許可）
const postalFields = document.querySelectorAll('input[name*="postalcode"]');
postalFields.forEach(field => {
    field.addEventListener('input', (e) => {
        // 入力された値から「数字」と「ハイフン」以外の文字を削除する
        let value = e.target.value.replace(/[^\d-]/g, '');
        e.target.value = value;
    });
});

    // 資本金カンマ区切り
    const capitalInput = document.getElementById('corporate_capital');
    if (capitalInput) {
        capitalInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/[^\d]/g, '');
            if (value) {
                value = parseInt(value).toLocaleString();
            }
            e.target.value = value;
        });
    }

    // 日付・ユーザー自動セット例
    const now = new Date().toISOString().slice(0, 19).replace('T', ' ');
    const currentUser = 'システム管理者'; // 本来は認証システムから取得
    const regDateInput = document.querySelector('input[name="registration_date"]');
    if (regDateInput) regDateInput.value = now;
    const updDateInput = document.querySelector('input[name="update_date"]');
    if (updDateInput) updDateInput.value = now;
    const regShainInput = document.querySelector('input[name="registration_shain"]');
    if (regShainInput) regShainInput.value = currentUser;
    const updShainInput = document.querySelector('input[name="update_shain"]');
    if (updShainInput) updShainInput.value = currentUser;
    if (updShainInput) updShainInput.value = currentUser;

    const ageSpan = document.getElementById('age_display');
    if (birthDateInput && seirekiSpan && warekiSpan && ageSpan) {
        function toWareki(ymd) {
            let y, m, d;
            if (/^\d{8}$/.test(ymd)) {
                y = parseInt(ymd.substr(0, 4), 10);
                m = parseInt(ymd.substr(4, 2), 10);
                d = parseInt(ymd.substr(6, 2), 10);
            } else {
                return "";
            }
            const eras = [
                { name: "令和", start: [2019, 5, 1] },
                { name: "平成", start: [1989, 1, 8] },
                { name: "昭和", start: [1926, 12, 25] },
                { name: "大正", start: [1912, 7, 30] },
                { name: "明治", start: [1868, 1, 25] }
            ];
            for (let era of eras) {
                const [ey, em, ed] = era.start;
                if (
                    y > ey ||
                    (y === ey && m > em) ||
                    (y === ey && m === em && d >= ed)
                ) {
                    let nen = y - ey + 1;
                    return `${era.name}${nen === 1 ? "元" : nen}年${m}月${d}日`;
                }
            }
            return "";
        }
        function calcAge(ymd) {
            if (!/^\d{8}$/.test(ymd)) return "";
            const y = parseInt(ymd.substr(0, 4), 10);
            const m = parseInt(ymd.substr(4, 2), 10);
            const d = parseInt(ymd.substr(6, 2), 10);
            const today = new Date();
            let age = today.getFullYear() - y;
            if (
                today.getMonth() + 1 < m ||
                (today.getMonth() + 1 === m && today.getDate() < d)
            ) {
                age--;
            }
            return age >= 0 ? `${age}歳` : "";
        }
        function updateBirthDateDisplay() {
            let v = birthDateInput.value.replace(/[^\d]/g, '');
            if (v.length === 8) {
                seirekiSpan.textContent = `${v.substr(0,4)}年${v.substr(4,2)}月${v.substr(6,2)}日`;
                warekiSpan.textContent = toWareki(v);
                ageSpan.textContent = calcAge(v);
            } else {
                seirekiSpan.textContent = "";
                warekiSpan.textContent = "";
                ageSpan.textContent = "";
            }
        }
        birthDateInput.addEventListener('input', updateBirthDateDisplay);
        birthDateInput.addEventListener('blur', updateBirthDateDisplay);
        updateBirthDateDisplay();
    }

    // === 設立年月日（法人）の和暦・西暦表示 ===
    const foundationDateInput = document.getElementById('corporate_foundationdate');
    const seirekiFoundationSpan = document.getElementById('seireki_foundationdate');
    const warekiFoundationSpan = document.getElementById('wareki_foundationdate');

    function toWareki(ymd) {
        let y, m, d;
        if (/^\d{8}$/.test(ymd)) {
            y = parseInt(ymd.substr(0, 4), 10);
            m = parseInt(ymd.substr(4, 2), 10);
            d = parseInt(ymd.substr(6, 2), 10);
        } else {
            return "";
        }
        const eras = [
            { name: "令和", start: [2019, 5, 1] },
            { name: "平成", start: [1989, 1, 8] },
            { name: "昭和", start: [1926, 12, 25] },
            { name: "大正", start: [1912, 7, 30] },
            { name: "明治", start: [1868, 1, 25] }
        ];
        for (let era of eras) {
            const [ey, em, ed] = era.start;
            if (
                y > ey ||
                (y === ey && m > em) ||
                (y === ey && m === em && d >= ed)
            ) {
                let nen = y - ey + 1;
                return `${era.name}${nen === 1 ? "元" : nen}年${m}月${d}日`;
            }
        }
        return "";
    }

    if (foundationDateInput && seirekiFoundationSpan && warekiFoundationSpan) {
        function updateFoundationDateDisplay() {
            let v = foundationDateInput.value.replace(/[^\d]/g, '');
            if (v.length === 8) {
                seirekiFoundationSpan.textContent = `${v.substr(0,4)}年${v.substr(4,2)}月${v.substr(6,2)}日`;
                warekiFoundationSpan.textContent = toWareki(v);
            } else {
                seirekiFoundationSpan.textContent = "";
                warekiFoundationSpan.textContent = "";
            }
        }
        foundationDateInput.addEventListener('input', updateFoundationDateDisplay);
        foundationDateInput.addEventListener('blur', updateFoundationDateDisplay);
        updateFoundationDateDisplay();
    }
});
