/**
 * =================================================================================
 * グローバル関数 (ポップアップウィンドウから呼び出される)
 * - この関数は、他のどの関数よりも先に、一番上に配置します。
 * =================================================================================
 */
function selectAgencyMaster(code, name) {
    // 表示用の入力欄に値をセット
    const codeDisplay = document.getElementById('agency_master_code_display');
    const nameDisplay = document.getElementById('agency_master_name');
    if (codeDisplay) codeDisplay.value = code;
    if (nameDisplay) nameDisplay.value = name;

    // 送信用の隠しフィールドに値をセット
    const hiddenCodeInput = document.getElementById('agency_master_code');
    if (hiddenCodeInput) hiddenCodeInput.value = code;
    
    // 既存支店リストを取得する関数を呼び出す
    fetchExistingBranches(code);
}

async function fetchExistingBranches(masterCode) {
    const listElement = document.getElementById('existing-branches-list');
    if (!listElement) return;

    listElement.innerHTML = '読み込み中...';
    try {
        const response = await fetch(`/api/get_branches/${masterCode}`);
        if (!response.ok) {
            throw new Error('サーバーとの通信に失敗しました。');
        }
        const branches = await response.json();
        updateBranchList(branches);
    } catch (error) {
        console.error('支店リストの取得に失敗しました:', error);
        listElement.innerHTML = '<span class="text-danger">支店リストの取得に失敗しました。</span>';
    }
}

function updateBranchList(branches) {
    const listElement = document.getElementById('existing-branches-list');
    if (!listElement) return;

    listElement.innerHTML = '';
    if (branches.length === 0) {
        listElement.textContent = '登録済みの支店はありません。';
    } else {
        const ul = document.createElement('ul');
        ul.className = 'list-unstyled mb-0 small';
        branches.forEach(branch => {
            const li = document.createElement('li');
            li.textContent = `・${branch.sub_name} (コード: ${branch.sub_code})`;
            ul.appendChild(li);
        });
        listElement.appendChild(ul);
    }
}

// カタカナを半角に変換する関数 (グローバルスコープに定義)
function toHalfWidthKana(str) {
    const kanaMap = {
        '。':'｡','「':'｢','」':'｣','、':'､','・':'･','ー':'ｰ',
        'ァ':'ｧ','ア':'ｱ','ィ':'ｨ','イ':'ｲ','ゥ':'ｩ','ウ':'ｳ','ェ':'ｪ','エ':'ｴ','ォ':'ｫ','オ':'ｵ',
        'カ':'ｶ','ガ':'ｶﾞ','キ':'ｷ','ギ':'ｷﾞ','ク':'ｸ','グ':'ｸﾞ','ケ':'ｹ','ゲ':'ｹﾞ','コ':'ｺ','ゴ':'ｺﾞ',
        'サ':'ｻ','ザ':'ｻﾞ','シ':'ｼ','ジ':'ｼﾞ','ス':'ｽ','ズ':'ｽﾞ','セ':'ｾ','ゼ':'ｾﾞ','ソ':'ｿ','ゾ':'ｿﾞ',
        'タ':'ﾀ','ダ':'ﾀﾞ','チ':'ﾁ','ヂ':'ﾁﾞ','ッ':'ｯ','ツ':'ﾂ','ヅ':'ﾂﾞ','テ':'ﾃ','デ':'ﾃﾞ','ト':'ﾄ','ド':'ﾄﾞ',
        'ナ':'ﾅ','ニ':'ﾆ','ヌ':'ﾇ','ネ':'ﾈ','ノ':'ﾉ',
        'ハ':'ﾊ','バ':'ﾊﾞ','パ':'ﾊﾟ','ヒ':'ﾋ','ビ':'ﾋﾞ','ピ':'ﾋﾟ','フ':'ﾌ','ブ':'ﾌﾞ','プ':'ﾌﾟ',
        'ヘ':'ﾍ','ベ':'ﾍﾞ','ペ':'ﾍﾟ','ホ':'ﾎ','ボ':'ﾎﾞ','ポ':'ﾎﾟ',
        'マ':'ﾏ','ミ':'ﾐ','ム':'ﾑ','メ':'ﾒ','モ':'ﾓ',
        'ヤ':'ﾔ','ャ':'ｬ','ユ':'ﾕ','ュ':'ｭ','ヨ':'ﾖ','ョ':'ｮ',
        'ラ':'ﾗ','リ':'ﾘ','ル':'ﾙ','レ':'ﾚ','ロ':'ﾛ',
        'ワ':'ﾜ','ヲ':'ｦ','ン':'ﾝ','ヴ':'ｳﾞ',
        'ぁ':'ｧ','あ':'ｱ','ぃ':'ｨ','い':'ｲ','ぅ':'ｩ','う':'ｳ','ぇ':'ｪ','え':'ｴ','ぉ':'ｫ','お':'ｵ',
        'か':'ｶ','が':'ｶﾞ','き':'ｷ','ぎ':'ｷﾞ','く':'ｸ','ぐ':'ｸﾞ','け':'ｹ','げ':'ｹﾞ','こ':'ｺ','ご':'ｺﾞ',
        'さ':'ｻ','ざ':'ｻﾞ','し':'ｼ','じ':'ｼﾞ','す':'ｽ','ず':'ｽﾞ','せ':'ｾ','ぜ':'ｾﾞ','そ':'ｿ','ぞ':'ｿﾞ',
        'た':'ﾀ','だ':'ﾀﾞ','ち':'ﾁ','ぢ':'ﾁﾞ','っ':'ｯ','つ':'ﾂ','づ':'ﾂﾞ','て':'ﾃ','で':'ﾃﾞ','と':'ﾄ','ど':'ﾄﾞ',
        'な':'ﾅ','に':'ﾆ','ぬ':'ﾇ','ね':'ﾈ','の':'ﾉ',
        'は':'ﾊ','ば':'ﾊﾞ','ぱ':'ﾊﾟ','ひ':'ﾋ','び':'ﾋﾞ','ぴ':'ﾋﾟ','ふ':'ﾌ','ぶ':'ﾌﾞ','ぷ':'ﾌﾟ',
        'へ':'ﾍ','べ':'ﾍﾞ','ぺ':'ﾍﾟ','ほ':'ﾎ','ぼ':'ﾎﾞ','ぽ':'ﾎﾟ',
        'ま':'ﾏ','み':'ﾐ','む':'ﾑ','め':'ﾒ','も':'ﾓ',
        'や':'ﾔ','ゃ':'ｬ','ゆ':'ﾕ','ゅ':'ｭ','よ':'ﾖ','ょ':'ｮ',
        'ら':'ﾗ','り':'ﾘ','る':'ﾙ','れ':'ﾚ','ろ':'ﾛ',
        'わ':'ﾜ','を':'ｦ','ん':'ﾝ','ゔ':'ｳﾞ'
    };
    return str
    // 全角スペース → 半角スペース
    .replace(/　/g, ' ')
    // kanaMapに含まれる任意の全角文字 → 半角文字
    .replace(/./g, match => kanaMap[match] || match);
}

// 和暦変換関数 (グローバルスコープに定義)
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

document.addEventListener('DOMContentLoaded', function () {
    // グローバル変数として宣言
    window.addressModalProcessing = false;
    
    // -----------------------------------------------------------------------------
    // ▼▼▼ 機能1：代理店本社 検索機能 ▼▼▼
    // -----------------------------------------------------------------------------
    const searchMasterBtn = document.getElementById('searchMasterBtn');
    if (searchMasterBtn) {
        searchMasterBtn.addEventListener('click', function() {
            const url = '/masters/agency_masterlist?context=popup';
            const windowName = 'SearchAgencyMaster';
            const windowFeatures = 'width=1000,height=700,scrollbars=yes,resizable=yes';
            window.open(url, windowName, windowFeatures);
        });
    }
    
    // -----------------------------------------------------------------------------
    // ▼▼▼ 機能2：タイプ切り替え ▼▼▼
    // -----------------------------------------------------------------------------
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

    // -----------------------------------------------------------------------------
    // ▼▼▼ 機能3：年齢自動計算 ▼▼▼
    // -----------------------------------------------------------------------------
    const birthdateInput = document.getElementById('individual_birthdate');
    const ageInput = document.getElementById('individual_age');
    if (birthdateInput && ageInput) {
        birthdateInput.addEventListener('change', () => {
            let v = birthdateInput.value.replace(/[^\d]/g, '');
            if (v.length === 8) {
                const birthdate = new Date(
                    v.substr(0, 4) + '-' + v.substr(4, 2) + '-' + v.substr(6, 2)
                );
                const today = new Date();
                let age = today.getFullYear() - birthdate.getFullYear();
                const monthDiff = today.getMonth() - birthdate.getMonth();
                if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthdate.getDate())) {
                    age--;
                }
                ageInput.value = age >= 0 ? age : '';
            }
        });
    }

    // -----------------------------------------------------------------------------
    // ▼▼▼ 機能4：和暦表示（生年月日） ▼▼▼
    // -----------------------------------------------------------------------------
    const warekiSpan = document.getElementById('wareki_birthdate');
    const seirekiSpan = document.getElementById('seireki_birthdate');
    const ageSpan = document.getElementById('age_display');
    
    // 和暦・西暦表示機能
    if (birthdateInput && seirekiSpan && warekiSpan) {
        function updateWareki() {
            let v = birthdateInput.value.replace(/[^\d]/g, '');
            if (v.length === 8) {
                warekiSpan.textContent = toWareki(v);
            } else if (/^\d{4}\/\d{2}\/\d{2}$/.test(birthdateInput.value)) {
                warekiSpan.textContent = toWareki(birthdateInput.value);
            } else {
                warekiSpan.textContent = "";
            }
        }
        birthdateInput.addEventListener('input', updateWareki);
        birthdateInput.addEventListener('blur', updateWareki);
        updateWareki();
    }

    // 生年月日8桁入力時に西暦・和暦を表示（西暦は「2025年04月11日」形式）
    if (birthdateInput && seirekiSpan && warekiSpan) {
        function updatebirthdateDisplay() {
            let v = birthdateInput.value.replace(/[^\d]/g, '');
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
        birthdateInput.addEventListener('input', updatebirthdateDisplay);
        birthdateInput.addEventListener('blur', updatebirthdateDisplay);
        updatebirthdateDisplay();
    }

    // 年齢表示
    if (birthdateInput && ageSpan) {
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
        function updateAgeDisplay() {
            let v = birthdateInput.value.replace(/[^\d]/g, '');
            if (v.length === 8) {
                ageSpan.textContent = calcAge(v);
            } else {
                ageSpan.textContent = "";
            }
        }
        birthdateInput.addEventListener('input', updateAgeDisplay);
        birthdateInput.addEventListener('blur', updateAgeDisplay);
        updateAgeDisplay();
    }

    // -----------------------------------------------------------------------------
    // ▼▼▼ 機能5：設立年月日（法人）の和暦・西暦表示 ▼▼▼
    // -----------------------------------------------------------------------------
    const foundationdateInput = document.getElementById('corporate_foundationdate');
    const seirekiFoundationSpan = document.getElementById('seireki_foundationdate');
    const warekiFoundationSpan = document.getElementById('wareki_foundationdate');

    if (foundationdateInput && seirekiFoundationSpan && warekiFoundationSpan) {
        function updateFoundationdateDisplay() {
            let v = foundationdateInput.value.replace(/[^\d]/g, '');
            if (v.length === 8) {
                seirekiFoundationSpan.textContent = `${v.substr(0,4)}年${v.substr(4,2)}月${v.substr(6,2)}日`;
                warekiFoundationSpan.textContent = toWareki(v);
            } else {
                seirekiFoundationSpan.textContent = "";
                warekiFoundationSpan.textContent = "";
            }
        }
        foundationdateInput.addEventListener('input', updateFoundationdateDisplay);
        foundationdateInput.addEventListener('blur', updateFoundationdateDisplay);
        updateFoundationdateDisplay();
    }

    // -----------------------------------------------------------------------------
    // ▼▼▼ 機能6：フォームバリデーション ▼▼▼
    // -----------------------------------------------------------------------------
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

    // -----------------------------------------------------------------------------
    // ▼▼▼ 機能7：電話番号入力の制御 ▼▼▼
    // -----------------------------------------------------------------------------
    const phoneFields = document.querySelectorAll('input[name*="tel"]');
    phoneFields.forEach(field => {
        field.addEventListener('input', (e) => {
            // 入力された値から「数字」と「ハイフン」以外の文字を削除する
            let value = e.target.value.replace(/[^\d-]/g, '');
            e.target.value = value;
        });
    });

    // -----------------------------------------------------------------------------
    // ▼▼▼ 機能8：郵便番号入力の制御 ▼▼▼
    // -----------------------------------------------------------------------------
    const postalFields = document.querySelectorAll('input[name*="postalcode"]');
    postalFields.forEach(field => {
        field.addEventListener('input', (e) => {
            // 入力された値から「数字」と「ハイフン」以外の文字を削除する
            let value = e.target.value.replace(/[^\d-]/g, '');
            e.target.value = value;
        });
    });

    // -----------------------------------------------------------------------------
    // ▼▼▼ 機能9：資本金カンマ区切り ▼▼▼
    // -----------------------------------------------------------------------------
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

    // -----------------------------------------------------------------------------
    // ▼▼▼ 機能10：住所検索 ▼▼▼
    // -----------------------------------------------------------------------------
    // 住所検索モーダル処理の準備
    const addressModalElement = document.getElementById('address-modal');
    if (addressModalElement) {
        const addressModal = new bootstrap.Modal(addressModalElement);
        const resultsList = document.getElementById('address-results-list');
        
        // モーダルのイベントリスナーを追加（安全に）
        addressModalElement.addEventListener('show.bs.modal', function() {
            window.addressModalProcessing = true;
        });
        
        addressModalElement.addEventListener('hidden.bs.modal', function() {
            setTimeout(() => {
                window.addressModalProcessing = false;
            }, 300);
        });
        
        // 元のrenderMenu関数を保存
        if (typeof window.renderMenu === 'function') {
            const originalRenderMenu = window.renderMenu;
            window.renderMenu = function(data) {
                if (window.addressModalProcessing) {
                    console.log('住所検索モーダル処理中のため、メニュー描画をスキップします');
                    return;
                }
                
                try {
                    originalRenderMenu(data);
                } catch (error) {
                    console.error('メニュー描画中にエラーが発生しました:', error);
                }
            };
        }
        
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
            // 既存のコードに安全処理を追加
            window.addressModalProcessing = true;
            
            if (!resultsList) {
                console.error('住所結果リスト要素が見つかりません');
                window.addressModalProcessing = false;
                return;
            }
            
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
    }

    // -----------------------------------------------------------------------------
    // ▼▼▼ 機能11：カタカナを半角に変換 ▼▼▼
    // -----------------------------------------------------------------------------
    const kanaFields = ['name_kana', 'shain_kana','property_name_kana','agency_master_name_kana','sub_name_kana'];
    kanaFields.forEach(fieldId => {
        const kanaInput = document.getElementById(fieldId);
        if (kanaInput) {
            kanaInput.addEventListener('blur', function () {
                const fullWidthKana = this.value;
                const halfWidthKana = toHalfWidthKana(fullWidthKana);
                this.value = halfWidthKana;
            });
        }
    });

    // -----------------------------------------------------------------------------
    // ▼▼▼ グローバルエラーハンドラー ▼▼▼
    // -----------------------------------------------------------------------------
    window.addEventListener('error', function(e) {
        if (window.addressModalProcessing && 
            e.message.includes('Cannot set properties of null')) {
            console.warn('モーダル処理中のエラーを無視します:', e.message);
            e.preventDefault();
            return true;
        }
    });
});


