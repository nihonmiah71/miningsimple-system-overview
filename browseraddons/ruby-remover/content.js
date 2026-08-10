(function() {
    // 1. Clean up ruby tags (remove Furigana)
    const rubies = document.querySelectorAll('ruby');
    rubies.forEach(ruby => {
        const rtsAndRps = ruby.querySelectorAll('rt, rp');
        rtsAndRps.forEach(el => el.remove());
        while (ruby.firstChild) {
            ruby.parentNode.insertBefore(ruby.firstChild, ruby);
        }
        ruby.parentNode.removeChild(ruby);
    });

    // CRUCIAL: Merges fragmented text nodes ("可愛" + "いい〜。") into a single string!
    document.body.normalize();

    // 2. Clean up "middle-block" paragraphs
    const middleBlocks = document.querySelectorAll('p.middle-block');
    middleBlocks.forEach(block => {
        let rawText = block.textContent;
        let cleanText = rawText.replace(/["„“”「」]/g, '').trim();
        cleanText = cleanText.replace(/\s+/g, ' ');

        if (cleanText.length > 0) {
            block.textContent = cleanText;
        }
    });
})();