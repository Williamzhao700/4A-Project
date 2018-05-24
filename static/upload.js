var myUploader = null;
var uploadImageAPI = '/api/upload';
var maxFileSize = 2048;
var imageExtensions = ['jpg', 'jpeg', 'png', 'bmp' ,'gif'];
var supportImgHTML = '<span class="glyphicon glyphicon-info-sign"></span> max file size 2M';

function escapeHtml(string) {
    return String(string).replace(/[&<>"'`=\/]/g, function (s) {
        return entityMap[s];
    });
}

function tryJSONParse(s) {
    try {
        return JSON.parse(s);
    }
    catch (e) {
        return s;
    }
}

function uploadCallback(msgElement, response) {
    if (response.success === true) {
        msgElement.html(shortSuccessText('Success'));
    } else {
        msgElement.html(shortFailText('Failed'));
    }
}

function bindMyFileUploadButton() {
    myUploader = new ss.SimpleUpload({
        button: $('#btnUpdateMyAvatar'),
        url: uploadImageAPI,
        name: 'image',
        maxSize: maxFileSize,
        allowedExtensions: imageExtensions,
        responseType: 'json',
        onSubmit: function () {
            $('#myProfileUploadTips').html(shortProcessingText('Uploading...'));
        },
        onSizeError: function() {
            $('#myProfileUploadTips').html(shortFailText('Max file size is 2M'));
        },
        onExtError: function() {
            $('#myProfileUploadTips').html(shortFailText('unsupported image type'));
        },
        onComplete: function (filename, response) {
            uploadCallback($('#myProfileUploadTips'), response);
        },
        onError: function (filename, response) {
            uploadCallback($('#myProfileUploadTips'), tryJSONParse(response));
        }
    });
}

$(bindMyFileUploadButton);

// $('#myProfileDialog').on('show.bs.modal', function (event) {
//     $('#myProfileUploadTips').html(supportImgHTML);
//     $('#myProfileStatus').removeClass('hidden');
//     $('#myProfileStatus').html(shortProcessingText('waiting...', true));
//     $('#btnUpdateMyProfile').attr('disabled', 'disabled');
// });

