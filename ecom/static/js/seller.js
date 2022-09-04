var cate_tree = {
    "Lifestyle": [
        ".",
        "Sport - Travel",
        "Book & Office Supplies",
        "Home Living"
    ],
    "ITC": [
        ".",
        "Electronic Accessories",
        "Camera",
        "IT"
    ],
    "Phones - Tablets": [
        ".",
        "Phones - Tablets"
    ],
    "Home Appliances": [
        ".",
        "TV",
        "Major Domestic Appliance",
        "Small Appliances"
    ],
    "CG": [
        ".",
        "Health - Beauty",
        "Mom - Baby",
        "FMCG"
    ],
    ".": [
        ".",
    ]
}

console.log(cate_tree)

// bind change event handler
$('#cate').change(function() {
    console.log(cate_tree)
// get the second dropdown
    $('#sub_cate').html(
        // get array by the selected value
        cate_tree[this.value]
        // iterate  and generate options
        .map(function(v) {
            // generate options with the array element
            value = v;
            if (v == '.') {
                text = "All"
            } else {
                text = v
            }
            return $('<option/>', {
            value: value,
            text: text
            })
        })
        )
        // trigger change event to generate second select tag initially
    }).change()

