$(function () {
    const sidebarLinkClickHandler = () => {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });
    }
    const scrollHandlerSidebarLinks = () => {
        $('main').scroll(function () {
            const contentSection = $('.section-container')
            let offset = contentSection.map(function () {
                let _ = $(this)
                let _id = _.attr('id')
                return {
                    offset: _.offset().top,
                    id: _id
                }
            })
            offset = offset.toArray()
            const closest = offset.reduce(function (prev, curr) {
                return (Math.abs(curr.offset) < Math.abs(prev.offset) ? curr : prev)
            })
            let inactiveNavItems = $('.nav-item').not('[data-ref="' + closest.id + '"]')
            const navItemPair = $('[data-ref="' + closest.id + '"]')
            inactiveNavItems.each(function () {
                $(this).removeClass('active')
            })
            navItemPair.each(function () {
                $(this).addClass('active')
            })
        });
    }

    sidebarLinkClickHandler()
    scrollHandlerSidebarLinks()
})
