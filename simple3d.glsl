---VERTEX SHADER---
#ifdef GL_ES
    precision highp float;
#endif

attribute vec3 v_pos;
attribute vec4 v_color;
attribute vec2 v_tc0;

uniform mat4 modelview_mat;
uniform mat4 projection_mat;

varying vec4 frag_color;
varying vec2 tex_coord0;

void main (void) {
    frag_color = v_color;
    tex_coord0 = v_tc0;
    gl_Position = projection_mat * modelview_mat * vec4(v_pos, 1.0);
}

---FRAGMENT SHADER---
#ifdef GL_ES
    precision highp float;
#endif

varying vec4 frag_color;
varying vec2 tex_coord0;
uniform sampler2D texture0;

void main (void) {
    // ถ้าพิกัด Texture ติดลบ แปลว่าเป็นพื้นกระดาน ให้ใช้สี Vertex (สีช่องตาราง)
    if (tex_coord0.x < -0.9) {
        gl_FragColor = frag_color;
    } else {
        // ดึงสีจากภาพ Texture ตัวหมากโดยตรง
        vec4 tex_col = texture2D(texture0, tex_coord0);
        
        // ตัดพิกเซลโปร่งใสทิ้ง
        if (tex_col.a < 0.1) {
            discard; 
        }
        
        // แสดงสีจากภาพจริง 100% ป้องกันปัญหาภาพกลายเป็นสีขาว
        gl_FragColor = tex_col;
    }
}