document.addEventListener('DOMContentLoaded', function() {
    const currentWordElement = document.getElementById('current-word');
    const definitionContainer = document.getElementById('definition-container');
    const definitionContent = document.getElementById('definition-content');
    const showDefinitionButton = document.getElementById('show-definition');
    const nextWordButton = document.getElementById('next-word');
    const editWordButton = document.getElementById('edit-word-btn');
    const markWordButton = document.getElementById('mark-word-btn');
    
    let currentWord = '';
    let definitionShown = false;
    
    // 获取随机单词
    function getRandomWord() {
        // 添加加载动画
        currentWordElement.classList.add('loading');
        currentWordElement.textContent = '加载中...';
        
        // 构建URL，传递上一个单词
        const url = `/get_random_word${currentWord ? '?prev_word=' + encodeURIComponent(currentWord) : ''}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    // 处理错误情况，例如"没有标注的单词"或"没有单词"
                    currentWordElement.textContent = data.word;
                    currentWordElement.classList.remove('loading');
                    currentWordElement.classList.add('word-appear');
                    
                    // 添加提示信息
                    let hintText = '没有标注的单词，请先标注一些单词';
                    if (data.word === 'No words available' || data.word === '暂无单词') {
                        hintText = '当前列表为空，请先添加一些单词';
                    }
                    
                    const noWordsHint = document.createElement('div');
                    noWordsHint.className = 'no-marked-hint';
                    noWordsHint.textContent = hintText;
                    noWordsHint.style.cssText = 'text-align: center; color: #8fa5c0; margin-top: 20px; font-size: 16px;';
                    
                    // 显示提示
                    if (!document.querySelector('.no-marked-hint')) {
                        currentWordElement.parentNode.appendChild(noWordsHint);
                    } else {
                        document.querySelector('.no-marked-hint').textContent = hintText;
                    }
                    
                    // 隐藏按钮组（而不是禁用）
                    const buttonGroup = document.querySelector('.button-group');
                    if (buttonGroup) {
                        buttonGroup.style.display = 'none';
                    }
                    
                    // 隐藏操作按钮
                    const wordActions = document.querySelector('.word-actions');
                    if (wordActions) {
                        wordActions.style.display = 'none';
                    }
                    
                    return;
                }
                
                // 移除可能存在的提示
                const existingHint = document.querySelector('.no-marked-hint');
                if (existingHint) {
                    existingHint.remove();
                }
                
                currentWord = data.word;
                
                // 移除加载动画，添加出现动画
                currentWordElement.classList.remove('loading');
                currentWordElement.classList.add('word-appear');
                currentWordElement.textContent = currentWord;
                
                // 恢复按钮组显示
                const buttonGroup = document.querySelector('.button-group');
                if (buttonGroup) {
                    buttonGroup.style.display = 'flex';
                }
                
                // 恢复操作按钮显示
                const wordActions = document.querySelector('.word-actions');
                if (wordActions) {
                    wordActions.style.display = 'flex';
                }
                
                // 恢复按钮状态
                showDefinitionButton.disabled = false;
                updateShowDefinitionButton(false);
                definitionShown = false;
                
                // 隐藏定义
                definitionContainer.classList.add('hidden');
                
                // 更新编辑按钮链接，添加from参数标识来源
                if (editWordButton) {
                    editWordButton.onclick = function() {
                        window.location.href = `/edit_word/${currentWord}?from=index`;
                    };
                    editWordButton.disabled = false;
                }
                
                // 更新标记按钮状态
                updateMarkButtonStatus();
                
                // 移除动画类，为下次动画做准备
                setTimeout(() => {
                    currentWordElement.classList.remove('word-appear');
                }, 500);
            })
            .catch(error => {
                console.error('获取单词错误:', error);
                currentWordElement.textContent = '加载失败，请重试';
                currentWordElement.classList.remove('loading');
                
                if (editWordButton) {
                    editWordButton.disabled = true;
                }
                if (markWordButton) {
                    markWordButton.disabled = true;
                }
            });
    }
    
    // 更新标记按钮状态
    function updateMarkButtonStatus() {
        if (!markWordButton || !currentWord) return;
        
        fetch(`/is_word_marked/${currentWord}`)
            .then(response => response.json())
            .then(data => {
                if (data.marked) {
                    markWordButton.classList.add('marked');
                    markWordButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>';
                } else {
                    markWordButton.classList.remove('marked');
                    markWordButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>';
                }
            })
            .catch(error => {
                console.error('获取标记状态错误:', error);
            });
    }
    
    // 更新显示/隐藏按钮状态
    function updateShowDefinitionButton(isShowing) {
        if (isShowing) {
            showDefinitionButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg> 关闭意思';
        } else {
            showDefinitionButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg> 查看意思';
        }
    }
    
    // 切换单词定义显示
    function toggleWordDefinition() {
        if (!currentWord) return;
        
        if (definitionShown) {
            // 隐藏定义
            definitionContainer.classList.add('hidden');
            updateShowDefinitionButton(false);
            definitionShown = false;
            return;
        }
        
        // 更改按钮状态
        showDefinitionButton.disabled = true;
        showDefinitionButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4M12 8h.01"></path></svg> 加载中...';
        
        fetch(`/get_word_definition/${currentWord}`)
            .then(response => response.json())
            .then(data => {
                // 清空之前的内容
                definitionContent.innerHTML = '';
                
                // 显示所有定义
                data.definitions.forEach(def => {
                    const defItem = document.createElement('div');
                    defItem.className = 'definition-item';
                    
                    // 词性
                    const partOfSpeech = document.createElement('span');
                    partOfSpeech.className = 'part-of-speech';
                    partOfSpeech.textContent = def.part_of_speech;
                    
                    // 意思
                    const meaning = document.createElement('div');
                    meaning.className = 'meaning';
                    meaning.textContent = def.meaning;
                    
                    // 添加词性和释义
                    const headerDiv = document.createElement('div');
                    headerDiv.className = 'definition-header';
                    headerDiv.appendChild(partOfSpeech);
                    headerDiv.appendChild(document.createTextNode(' '));
                    defItem.appendChild(headerDiv);
                    defItem.appendChild(meaning);
                    
                    // 例句
                    if (def.example && def.example.trim()) {
                        const example = document.createElement('div');
                        example.className = 'example';
                        example.textContent = def.example;
                        defItem.appendChild(example);
                    }
                    
                    // 笔记
                    if (def.note && def.note.trim()) {
                        const note = document.createElement('div');
                        note.className = 'note';
                        note.textContent = def.note;
                        defItem.appendChild(note);
                    }
                    
                    definitionContent.appendChild(defItem);
                });
                
                // 更改按钮状态
                showDefinitionButton.disabled = false;
                updateShowDefinitionButton(true);
                definitionShown = true;
                
                // 显示定义容器
                definitionContainer.classList.remove('hidden');
                definitionContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            })
            .catch(error => {
                console.error('获取定义错误:', error);
                showDefinitionButton.disabled = false;
                showDefinitionButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg> 重试';
            });
    }
    
    // 标记/取消标记单词
    function toggleMarkWord() {
        if (!currentWord || !markWordButton) return;
        
        const isCurrentlyMarked = markWordButton.classList.contains('marked');
        const action = isCurrentlyMarked ? 'unmark' : 'mark';
        
        fetch(`/${action}_word/${currentWord}`, {
            method: 'POST'
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateMarkButtonStatus();
                }
            })
            .catch(error => {
                console.error('标记单词错误:', error);
            });
    }
    
    // 绑定事件
    showDefinitionButton.addEventListener('click', toggleWordDefinition);
    nextWordButton.addEventListener('click', getRandomWord);
    
    if (markWordButton) {
        markWordButton.addEventListener('click', toggleMarkWord);
    }
    
    // 键盘快捷键
    document.addEventListener('keydown', function(e) {
        // 空格键查看/关闭释义
        if (e.code === 'Space' && !showDefinitionButton.disabled) {
            e.preventDefault(); // 防止页面滚动
            toggleWordDefinition();
        }
        
        // 右箭头键获取下一个单词
        if (e.code === 'ArrowRight') {
            e.preventDefault();
            getRandomWord();
        }
    });
    
    // 页面加载后恢复状态或获取第一个单词
    restorePageState();
    
    // 保存页面状态到localStorage
    function savePageState() {
        const state = {
            currentWord: currentWord,
            prevWord: document.getElementById('prevWordText').textContent.trim(),
            timestamp: Date.now()
        };
        
        localStorage.setItem('indexPageState', JSON.stringify(state));
    }
    
    // 恢复页面状态
    function restorePageState() {
        const savedState = localStorage.getItem('indexPageState');
        
        if (savedState) {
            try {
                const state = JSON.parse(savedState);
                
                // 如果保存的状态有效（不是初始状态且不超过1小时）
                const oneHour = 60 * 60 * 1000;
                if (state.currentWord && 
                    state.currentWord !== '点击"下一个"开始' && 
                    state.currentWord !== '加载中...' &&
                    (Date.now() - state.timestamp) < oneHour) {
                    
                    // 恢复当前单词
                    currentWordElement.textContent = state.currentWord;
                    currentWord = state.currentWord;
                    
                    // 恢复上一个单词
                    if (state.prevWord && state.prevWord !== '-') {
                        document.getElementById('prevWordText').textContent = state.prevWord;
                    }
                    
                    // 更新编辑按钮
                    if (editWordButton) {
                        editWordButton.onclick = function() {
                            window.location.href = `/edit_word/${currentWord}?from=index`;
                        };
                        editWordButton.disabled = false;
                    }
                    
                    // 更新标记按钮状态
                    updateMarkButtonStatus();
                    
                    return; // 不需要获取新单词
                }
            } catch (e) {
                console.error('恢复页面状态失败:', e);
            }
        }
        
        // 如果没有保存的状态或状态无效，获取第一个单词
        getRandomWord();
    }
    
    // 监听页面即将卸载事件，保存状态
    window.addEventListener('beforeunload', function() {
        savePageState();
    });
    
    // 监听页面可见性变化，在隐藏时保存状态
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            savePageState();
        }
    });
}); 