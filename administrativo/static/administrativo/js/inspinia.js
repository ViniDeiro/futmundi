/*
 *
 *   INSPINIA - Responsive Admin Theme
 *   version 2.9.2
 *
 */


$(document).ready(function () {


    // Fast fix bor position issue with Propper.js
    // Will be fixed in Bootstrap 4.1 - https://github.com/twbs/bootstrap/pull/24092
    Popper.Defaults.modifiers.computeStyle.gpuAcceleration = false;


    // Add body-small class if window less than 768px
    if ($(window).width() < 769) {
        $('body').addClass('body-small')
    } else {
        $('body').removeClass('body-small')
    }

    // MetisMenu
    var sideMenu = $('#side-menu').metisMenu();

    // Collapse ibox function
    $('.collapse-link').on('click', function (e) {
        e.preventDefault();
        var ibox = $(this).closest('div.ibox');
        var button = $(this).find('i');
        var content = ibox.children('.ibox-content');
        content.slideToggle(200);
        button.toggleClass('fa-chevron-up').toggleClass('fa-chevron-down');
        ibox.toggleClass('').toggleClass('border-bottom');
        setTimeout(function () {
            ibox.resize();
            ibox.find('[id^=map-]').resize();
        }, 50);
    });

    // Close ibox function
    $('.close-link').on('click', function (e) {
        e.preventDefault();
        var content = $(this).closest('div.ibox');
        content.remove();
    });

    // Fullscreen ibox function
    $('.fullscreen-link').on('click', function (e) {
        e.preventDefault();
        var ibox = $(this).closest('div.ibox');
        var button = $(this).find('i');
        $('body').toggleClass('fullscreen-ibox-mode');
        button.toggleClass('fa-expand').toggleClass('fa-compress');
        ibox.toggleClass('fullscreen');
        setTimeout(function () {
            $(window).trigger('resize');
        }, 100);
    });

    // Close menu in canvas mode
    $('.close-canvas-menu').on('click', function (e) {
        e.preventDefault();
        $("body").toggleClass("mini-navbar");
        SmoothlyMenu();
    });

    // Run menu of canvas
    $('body.canvas-menu .sidebar-collapse').slimScroll({
        height: '100%',
        railOpacity: 0.9
    });

    // Open close right sidebar
    $('.right-sidebar-toggle').on('click', function (e) {
        e.preventDefault();
        $('#right-sidebar').toggleClass('sidebar-open');
    });

    // Initialize slimscroll for right sidebar
    $('.sidebar-container').slimScroll({
        height: '100%',
        railOpacity: 0.4,
        wheelStep: 10
    });

    // Open close small chat
    $('.open-small-chat').on('click', function (e) {
        e.preventDefault();
        $(this).children().toggleClass('fa-comments').toggleClass('fa-times');
        $('.small-chat-box').toggleClass('active');
    });

    // Initialize slimscroll for small chat
    $('.small-chat-box .content').slimScroll({
        height: '234px',
        railOpacity: 0.4
    });

    // Small todo handler
    $('.check-link').on('click', function () {
        var button = $(this).find('i');
        var label = $(this).next('span');
        button.toggleClass('fa-check-square').toggleClass('fa-square-o');
        label.toggleClass('todo-completed');
        return false;
    });

    // Append config box / Only for demo purpose
    // Uncomment on server mode to enable XHR calls
    //$.get("skin-config.html", function (data) {
    //    if (!$('body').hasClass('no-skin-config'))
    //        $('body').append(data);
    //});

    // Minimalize menu
    $('.navbar-minimalize').on('click', function (event) {
        event.preventDefault();
        $("body").toggleClass("mini-navbar");
        SmoothlyMenu();

    });

    // Tooltips demo
    $('.tooltip-demo').tooltip({
        selector: "[data-toggle=tooltip]",
        container: "body"
    });


    // Move right sidebar top after scroll
    $(window).scroll(function () {
        if ($(window).scrollTop() > 0 && !$('body').hasClass('fixed-nav')) {
            $('#right-sidebar').addClass('sidebar-top');
        } else {
            $('#right-sidebar').removeClass('sidebar-top');
        }
    });

    $("[data-toggle=popover]")
        .popover();

    // Add slimscroll to element
    $('.full-height-scroll').slimscroll({
        height: '100%'
    })
});

// Minimalize menu when screen is less than 768px
$(window).bind(" resize", function () {
    if ($(this).width() < 769) {
        $('body').addClass('body-small')
    } else {
        $('body').removeClass('body-small')
    }
});

// Fixed Sidebar
$(window).bind("load", function () {
    if ($("body").hasClass('fixed-sidebar')) {
        $('.sidebar-collapse').slimScroll({
            height: '100%',
            railOpacity: 0.9
        });
    }
});



// Minimalize menu when screen is less than 768px
$(window).bind("load resize", function () {
    if ($(this).width() < 769) {
        $('body').addClass('body-small')
    } else {
        $('body').removeClass('body-small')
    }
});

// Local Storage functions
// Set proper body class and plugins based on user configuration
$(document).ready(function () {
    if (localStorageSupport()) {

        var collapse = localStorage.getItem("collapse_menu");
        var fixedsidebar = localStorage.getItem("fixedsidebar");
        var fixednavbar = localStorage.getItem("fixednavbar");
        var boxedlayout = localStorage.getItem("boxedlayout");
        var fixedfooter = localStorage.getItem("fixedfooter");

        var body = $('body');

        if (fixedsidebar == 'on') {
            body.addClass('fixed-sidebar');
            $('.sidebar-collapse').slimScroll({
                height: '100%',
                railOpacity: 0.9
            });
        }

        if (collapse == 'on') {
            if (body.hasClass('fixed-sidebar')) {
                if (!body.hasClass('body-small')) {
                    body.addClass('mini-navbar');
                }
            } else {
                if (!body.hasClass('body-small')) {
                    body.addClass('mini-navbar');
                }

            }
        }

        if (fixednavbar == 'on') {
            $(".navbar-static-top").removeClass('navbar-static-top').addClass('navbar-fixed-top');
            body.addClass('fixed-nav');
        }

        if (boxedlayout == 'on') {
            body.addClass('boxed-layout');
        }

        if (fixedfooter == 'on') {
            $(".footer").addClass('fixed');
        }
    }
});

// check if browser support HTML5 local storage
function localStorageSupport() {
    return (('localStorage' in window) && window['localStorage'] !== null)
}

// For demo purpose - animation css script
function animationHover(element, animation) {
    element = $(element);
    element.hover(
        function () {
            element.addClass('animated ' + animation);
        },
        function () {
            //wait for animation to finish before removing classes
            window.setTimeout(function () {
                element.removeClass('animated ' + animation);
            }, 2000);
        });
}

function SmoothlyMenu() {
    if (!$('body').hasClass('mini-navbar') || $('body').hasClass('body-small')) {
        // Hide menu in order to smoothly turn on when maximize menu
        $('#side-menu').hide();
        // For smoothly turn on menu
        setTimeout(
            function () {
                $('#side-menu').fadeIn(400);
            }, 200);
    } else if ($('body').hasClass('fixed-sidebar')) {
        $('#side-menu').hide();
        setTimeout(
            function () {
                $('#side-menu').fadeIn(400);
            }, 100);
    } else {
        // Remove all inline style from jquery fadeIn function to reset menu state
        $('#side-menu').removeAttr('style');
    }
}

// Dragable panels
function WinMove() {
    var element = "[class*=col]";
    var handle = ".ibox-title";
    var connect = "[class*=col]";
    $(element).sortable(
        {
            handle: handle,
            connectWith: connect,
            tolerance: 'pointer',
            forcePlaceholderSize: true,
            opacity: 0.8
        })
        .disableSelection();
}

// Função auto-executável para garantir que os estilos e o layout sejam mantidos após redirecionamentos
(function() {
    // Função para adicionar timestamp para evitar cache
    function addCacheBuster(url) {
        // Não modificar se não for uma URL
        if (!url || typeof url !== 'string') return url;

        // Adicionar parâmetro de timestamp para evitar cache
        var separator = url.indexOf('?') !== -1 ? '&' : '?';
        return url + separator + '_ts=' + new Date().getTime();
    }

    // Sobrescrever a função location.href para adicionar cache buster
    var originalLocationDescriptor = Object.getOwnPropertyDescriptor(window, 'location');
    var proxiedLocation = {};

    // Criar um proxy para window.location para interceptar redirecionamentos
    Object.defineProperty(window, 'location', {
        get: function() {
            return proxiedLocation;
        },
        set: function(url) {
            // Quando o location é definido diretamente, adicionar cache buster
            console.log("Redirecionando com cache buster:", url);
            originalLocationDescriptor.set.call(window, addCacheBuster(url));
            return url;
        },
        configurable: true
    });

    // Sobrescrever o window.location.href para adicionar cache buster
    Object.defineProperty(proxiedLocation, 'href', {
        get: function() {
            return originalLocationDescriptor.get.call(window).href;
        },
        set: function(url) {
            // Armazenar um identificador de redirecionamento no sessionStorage
            sessionStorage.setItem('lastRedirect', new Date().getTime());
            
            // Usar o valor original com cache buster
            console.log("Redirecionando (href) com cache buster:", url);
            originalLocationDescriptor.get.call(window).href = addCacheBuster(url);
            return url;
        },
        configurable: true
    });

    // Armazenar a hora do último unload para detectar navegação para trás/frente
    window.addEventListener('beforeunload', function() {
        sessionStorage.setItem('lastUnload', new Date().getTime());
    });

    // Verificar ao carregar a página se precisamos recarregar recursos
    document.addEventListener('DOMContentLoaded', function() {
        var lastUnload = sessionStorage.getItem('lastUnload');
        var lastRedirect = sessionStorage.getItem('lastRedirect');
        var now = new Date().getTime();
        var timeSinceUnload = lastUnload ? now - parseInt(lastUnload) : 99999;
        
        // Se a última ação foi um unload (navegação para trás/frente) e não um redirecionamento intencional
        if (timeSinceUnload < 5000 && (!lastRedirect || (now - parseInt(lastRedirect) > 5000))) {
            console.log("Navegação detectada, forçando recarregamento de CSS");
            
            // Recarregar CSS para garantir que o layout está correto
            var links = document.querySelectorAll("link[rel='stylesheet']");
            links.forEach(function(link) {
                // Criar novo link para forçar recarregamento
                var newLink = document.createElement('link');
                newLink.rel = 'stylesheet';
                newLink.href = addCacheBuster(link.href);
                document.head.appendChild(newLink);
            });
        }
        
        // Verificar se o CSS foi carregado corretamente
        setTimeout(function() {
            // Verificar se o elemento body tem o estilo esperado
            var bodyStyles = window.getComputedStyle(document.body);
            var bodyBgColor = bodyStyles.backgroundColor;
            
            // Se o background for transparente ou não foi definido, é provável que o CSS não foi carregado
            if (bodyBgColor === 'rgba(0, 0, 0, 0)' || bodyBgColor === 'transparent') {
                console.log("Detectado problema no carregamento de CSS. Recarregando página...");
                // Recarregar a página com parâmetro de cache buster
                window.location.href = addCacheBuster(window.location.href);
            }
        }, 500);
    });
})();


