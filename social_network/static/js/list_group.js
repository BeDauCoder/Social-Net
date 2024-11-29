console.log("list_group.js loaded successfully");

const tabs = document.querySelectorAll('.tab_btn');
const contents = document.querySelectorAll('.content');

tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => {
        tabs.forEach(tab => tab.classList.remove('active'));
        tab.classList.add('active');
        
        contents.forEach(content => content.classList.remove('active'));
        contents[index].classList.add('active');
    });
});
// Carousel loop
let imageCarouselItems = document.querySelectorAll('#imageCarousel .carousel-item');
    imageCarouselItems.forEach((el) => {
        const minPerSlide = 6;
        let next = el.nextElementSibling;
        for (var i = 1; i < minPerSlide; i++) {
            if (!next) {
                next = imageCarouselItems[0];
            }
            let cloneChild = next.cloneNode(true);
            el.appendChild(cloneChild.children[0]);
            next = next.nextElementSibling;
        }
    });