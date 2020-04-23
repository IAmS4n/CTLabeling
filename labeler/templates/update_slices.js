{% for slice in slices %}
    {% if slice.img %}
        document.getElementById("img_{{slice.z}}").src = "{{slice.img}}";
        document.getElementById("z_{{ slice.z }}_positive").name = "z_{{ slice.z }}_{{slice.hmac}}";
        document.getElementById("z_{{ slice.z }}_negative").name = "z_{{ slice.z }}_{{slice.hmac}}";
        document.getElementById("tbl_row_{{slice.z}}").style.display = "";

    {% endif %}
{% endfor %}

document.getElementById("send_time").value += "_{{send_time}}";
document.getElementById("rnd").value += "_{{rnd}}";
change_selected_view();
