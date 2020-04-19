{% for slice in slices %}
    document.getElementById("img_{{slice.z}}_big").src = "{{slice.img}}";
{% endfor %}

document.getElementById("send_time").value += "_{{send_time}}";
document.getElementById("rnd").value += "_{{rnd}}";
