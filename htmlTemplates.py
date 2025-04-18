css = '''
<style>
.chat-message {
    padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex
}
.chat-message.user {
    background-color: #2b313e
}
.chat-message.bot {
    background-color: #475063
}
.chat-message .avatar {
  width: 20%;
}
.chat-message .avatar img {
  max-width: 78px;
  max-height: 78px;
  border-radius: 50%;
  object-fit: cover;
}
.chat-message .message {
  width: 80%;
  padding: 0 1.5rem;
  color: #fff;
}
</style>
'''

bot_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <img src="https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEh_kzb_6j188hVsr5RHOjaG0geNq2tRqDwHH-bc60R1DRa-hjXzrLqQjP6Zr4dAixSqcnfsqKLuisOcvqDiFviKTpBM29IhGLpqpiF3mvqQ3GElJlik-VsfRRlROuStfzvFatiCVdUcPw8TxcmiMzwTWZGMPvDmZNkHtotcRhkz6H5CCAutlwDkxuHcotvB/s16000-rw/Robotics%20and%20Artificial%20Intelligence%20(AI).webp" style="max-height: 78px; max-width: 78px; border-radius: 50%; object-fit: cover;">
    </div>
    <div class="message">{{MSG}}</div>
</div>
'''

user_template = '''
<div class="chat-message user">
    <div class="avatar">
        <img src="https://i.pinimg.com/736x/8b/16/7a/8b167af653c2399dd93b952a48740620.jpg">
    </div>    
    <div class="message">{{MSG}}</div>
</div>
'''
