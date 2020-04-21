{% for slice in slices %}
    {% if slice.img %}
        document.getElementById("img_{{slice.z}}").src = "{{slice.img}}";
        document.getElementById("tbl_row_{{slice.z}}").style.display = "";

    {% endif %}
{% endfor %}

document.getElementById("send_time").value += "_{{send_time}}";
document.getElementById("rnd").value += "_{{rnd}}";
change_selected_view();
