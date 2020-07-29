function popImage(filename) {
  $.magnificPopup.open({
    items: {
      src: "img/" + filename
    },
    type: 'image'

    // You may add options here, they're exactly the same as for $.fn.magnificPopup call
    // Note that some settings that rely on click event (like disableOn or midClick) will not work here
  }, 0);
}


var options = {
  urlForSize: function(filename, size) {
    return 'thumbnail/' + filename;
  },
  onClickHandler: function(filename) {
    popImage(filename);
  },
  primaryImageBufferHeight: 2000,
  secondaryImageBufferHeight: 500,
};

var imageData = [];
var searchTokens = {};
var pig;

function onlyUnique(value, index, self) {
  return self.indexOf(value) === index;
}

function processData(allText) {
  var allTextLines = allText.split(/\r\n|\n/);
  var imageData = [];

  for (var i=0; i<allTextLines.length; i++) {
      var data = allTextLines[i].split(',');
      var filename = data[0].replace("\"", "").replace("\"", "").replace('#', '%23')
      var tokens = []
      if (data.length == 4) {
        tokens = data[3].split(';')
      }
      imageData.push({filename: filename, aspectRatio: data[1], datetime: data[2], searchTokens: tokens})
  }

  searchTokens = [...new Set(searchTokens)]
  return imageData
}

function processSearchTokens(allText) {
  var allTextLines = allText.split(/\r\n|\n/);
  var tokens = [];

  for (var i=0; i<allTextLines.length; i++) {
    tokens.push(allTextLines[i])
  }

  return tokens;
}

function showImages(year) {
  // remove old images
  if (pig) pig.disable()
  $("#pig").empty()
  $("#pig").empty()

  images = imageData;
  if (year) {
    images = []
    for (var i=0; i<imageData.length; i++) {
      if (new Date(imageData[i].datetime).getFullYear() == year) {
        images.push(imageData[i]);
      }
    }
  }

  pig = new Pig(images, options).enable();
}

function showImagesSearch(searchToken) {
  // remove old images
  if (pig) pig.disable()
  $("#pig").empty()
  $("#pig").empty()

  images = imageData;
  images = []
  for (var i=0; i<imageData.length; i++) {
    if (imageData[i].searchTokens.includes(searchToken)) {
      images.push(imageData[i]);
    }
  }
  pig = new Pig(images, options).enable();
}

var years = []
var searchTokens = []
var output = []

$.ajax({
    type: 'GET',
    url: 'photos.csv',
    contentType: 'csv',
    cache: false,
    processData: false,
    async: false,
    success: function(data) {
      imageData = processData(data)
      // figure out the years
      var dates = []
      var years = []
      for (var i=0; i<imageData.length; i++) {
        d = new Date(Date.parse(imageData[i].datetime));
        dates.push(d);
        years.push(d.getFullYear());
      }

      var flags = [], output = []
      for(var i=0; i<years.length; i++) {
        if( flags[years[i]]) continue;
        flags[years[i]] = true;
        output.push(years[i]);
      }


      p = $("#header-p")
      for (var i=0; i<output.length; i++) {
        if (!isNaN(output[i])) {
          var text = "<span><a style=\"font-size: 20px\" href=\"javascript:showImages(" + output[i] + ");\">" + output[i] + "</a>&nbsp;&nbsp;</span>";
          p.append(text)
        }
      }

      d = new Date();
      showImages(d.getFullYear());
    },
});

$.ajax({
    type: 'GET',
    url: 'search-tokens.csv',
    contentType: 'csv',
    cache: false,
    processData: false,
    async: false,
    success: function(data) {
      tokens = processSearchTokens(data);

      $('#search').autocomplete({source: tokens});
    },
});

$('#search').on('keypress',function(e) {
  if(e.which == 13) {
    showImagesSearch($('#search').val());
  }
});

$("#search").on("autocompleteselect", function( event, ui ) {
  showImagesSearch($('#search').val());
});