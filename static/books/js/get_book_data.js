// taken from stackoverflow to load jquery in external js file
if (typeof jQuery === "undefined") {
    var script = document.createElement('script');
    script.src = 'http://code.jquery.com/jquery-latest.min.js';
    script.type = 'text/javascript';
    document.getElementsByTagName('head')[0].appendChild(script);
}

addSubject = function(currentValue) {
  console.log("adding "+currentValue);
  $(".tags").append("<li>"+currentValue+"</li>");
}

window.onload = function() {
    $.ajax({
          url: '/books/json',
          type: 'get',
          data: {
                work_id: $('.work_id').text(),
                },
          success: function(response) {
                    $('.title').text(response.title);

                    if (response.description != null) {
                      $('.description').text(response.description);
                    }

                    if (response.authors != null) {
                      $('.bookauthors').text(response.authors);
                    }
                    if (response.first_publish_date != null) {
                      $('.year').text(response.first_publish_date);
                    }
                    if (response.cover != null) {
                      $('.cover').attr("src", response.cover);
                    }
                    response.subjects.forEach(addSubject);
                },
          error: function() {
                  window.location.href = "/";
                }
            });
}
