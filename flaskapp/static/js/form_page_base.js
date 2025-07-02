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
    const isNewMode = document.title.includes("新規");
    
    

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

/* ▼▼▼ form_page_base.jsの住所検索関連のコードは、最終的に以下のようになります ▼▼▼ */

document.addEventListener('DOMContentLoaded', function () {

    // --- 住所検索機能の初期化 ---
    const addressModalElement = document.getElementById('address-modal');
    if (!addressModalElement) return;

    const addressModal = new bootstrap.Modal(addressModalElement);
    const resultsList = document.getElementById('address-results-list');
    
    // ページ内にある、すべての住所検索グループを対象に処理を適用
    document.querySelectorAll('.address-lookup-group').forEach(group => {
        // --- 郵便番号からの検索 ---
        const searchBtn = group.querySelector('.address-search-btn');
        const postalCodeInput = group.querySelector('.postal-code-input');

        if (searchBtn && postalCodeInput) {
            searchBtn.addEventListener('click', async () => {
                const postalCode = postalCodeInput.value;
                if (!postalCode) {
                    alert('郵便番号を入力してください。');
                    return;
                }
                try {
                    const response = await fetch(`/api/search_address_by_postal?postal_code=${encodeURIComponent(postalCode)}`);
                    if (!response.ok) throw new Error('サーバーとの通信に失敗しました。');
                    const results = await response.json();
                    showAddressModal(results, group);
                } catch (error) {
                    console.error("住所検索エラー:", error);
                    alert('住所の検索中にエラーが発生しました。');
                }
            });
        }

        // --- 住所からの逆引き検索 ---
        const reverseSearchBtn = group.querySelector('.reverse-address-search-btn');
        const prefectureInput = group.querySelector('.prefecture-output');
        const cityInput = group.querySelector('.city-output');
        const townInput = group.querySelector('.town-output');

        if (reverseSearchBtn) {
            reverseSearchBtn.addEventListener('click', async () => {
                const prefecture = prefectureInput ? prefectureInput.value : '';
                const city = cityInput ? cityInput.value : '';
                const town = townInput ? townInput.value : '';

                if (!prefecture && !city && !town) {
                    alert('都道府県、市区町村、町名のいずれかを入力してください。');
                    return;
                }
                const params = new URLSearchParams();
                if (prefecture) params.append('prefecture', prefecture);
                if (city) params.append('city', city);
                if (town) params.append('town', town);
                try {
                    const response = await fetch(`/api/search_postal_by_address?${params.toString()}`);
                    if (!response.ok) throw new Error('サーバーとの通信に失敗しました。');
                    const results = await response.json();
                    showAddressModal(results, group);
                } catch (error) {
                    console.error("逆引き検索エラー:", error);
                    alert('郵便番号の検索中にエラーが発生しました。');
                }
            });
        }
    });

    // 住所候補をモーダルに表示する関数
    function showAddressModal(results, targetGroup) {
        resultsList.innerHTML = ''; // 前回の結果をクリア

        if (results.length === 0) {
            resultsList.innerHTML = '<li class="list-group-item">該当する住所が見つかりませんでした。</li>';
        } else {
            results.forEach(addr => {
                const a = document.createElement('a');
                a.href = '#';
                a.className = 'list-group-item list-group-item-action';
                a.textContent = `〒${addr.postal_code} ${addr.prefecture} ${addr.city} ${addr.town}`;
                
                // data属性に全データを埋め込む
                a.dataset.postalCode = addr.postal_code; // 郵便番号もdata属性に追加
                a.dataset.prefecture = addr.prefecture;
                a.dataset.city = addr.city;
                a.dataset.town = addr.town;
                a.dataset.cityKana = addr.city_kana;
                a.dataset.townKana = addr.town_kana;

                a.addEventListener('click', (e) => {
                    e.preventDefault();
                    populateAddressFields(e.target.dataset, targetGroup);
                    addressModal.hide();
                });

                resultsList.appendChild(a);
            });
        }
        addressModal.show();
    }

    // フォームの各欄に住所情報を反映させる関数
    function populateAddressFields(data, targetGroup) {
        const postalCodeInput = targetGroup.querySelector('.postal-code-input');
        const prefectureInput = targetGroup.querySelector('.prefecture-output');
        const cityInput = targetGroup.querySelector('.city-output');
        const townInput = targetGroup.querySelector('.town-output');
        const cityKanaSpan = targetGroup.querySelector('.city-kana-output');
        const townKanaSpan = targetGroup.querySelector('.town-kana-output');

        if (postalCodeInput) postalCodeInput.value = data.postalCode || ''; // 郵便番号も反映
        if (prefectureInput) prefectureInput.value = data.prefecture || '';
        if (cityInput) cityInput.value = data.city || '';
        if (townInput) townInput.value = data.town || '';
        if (cityKanaSpan) cityKanaSpan.textContent = data.cityKana || '';
        if (townKanaSpan) townKanaSpan.textContent = data.townKana || '';
    }
});