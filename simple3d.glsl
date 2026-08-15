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

void main(void) {
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

void main(void) {
    // กรณีเป็นพื้นกระดาน (เรากำหนด UV ไว้ที่ -1.0)
    if (tex_coord0.x < -0.5) {
        gl_FragColor = frag_color;
    } else {
        // กรณีเป็นตัวหมาก ให้ดึงสีจาก Texture โดยตรง
        vec4 tex_col = texture2D(texture0, tex_coord0);
        
        // ตัดพื้นหลังที่โปร่งใสทิ้งไป
        if (tex_col.a < 0.1) {
            discard;
        }
        
        gl_FragColor = tex_col;
    }
}