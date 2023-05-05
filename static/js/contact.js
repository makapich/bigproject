$(function () {

  var loadForm = function () {
    var btn = $(this);
    $.ajax({
      url: btn.attr("data-url"),
      type: 'get',
      dataType: 'json',
      beforeSend: function () {
        $("#modal-contact").modal("show");
      },
      success: function (data) {
        $("#modal-contact .modal-content").html(data.html_form);
      }
    });
  };

  var saveForm = function () {
    var form = $(this);
    $.ajax({
        url: form.attr("action"),
        data: form.serialize(),
        type: form.attr("method"),
        dataType: 'json',
        success: function (data) {
            if (data.form_is_valid) {
                $("#modal-contact .modal-content").html("<p>Thanks for contacting us!</p>");
                setTimeout(function() {
                    $("#modal-contact").modal("hide");
                }, 1000);
            } else {
                $("#modal-contact .modal-content").html(data.html_form);
            }
        }
    });
    return false;
  };

  $(".js-contact").click(loadForm);
  $("#modal-contact").on("submit", ".js-contact-us-form", saveForm);

});