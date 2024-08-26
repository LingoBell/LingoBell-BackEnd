module.exports = {
  apps : [
    {
      name: "backend",  // FastAPI 애플리케이션 이름
      script: "/home/ubuntu/lingobell_backend/source/myenv/bin/python3",
      args: "-m uvicorn app.main:app --host 0.0.0.0 --port 8000",  // FastAPI 실행 인자
      // interpreter: "/home/ubuntu/lingobell_backend/source/myenv/bin/python3",
      env: {
        "PYTHONUNBUFFERED": "1",
        "PATH": "/home/ubuntu/lingobell_backend/source/myenv/bin:$PATH",
      },
    },
  ],

  deploy : {
    production : {
      user : 'ubuntu',
      host : '13.124.160.18',
      ref  : 'origin/main',
      repo : 'https://github.com/LingoBell/LingoBell-BackEnd.git',
      path : '/home/ubuntu/lingobell_backend',
      key: "~/develop/lingobell-EC2.pem",
      'post-deploy' : 'source myenv/bin/activate && pip install -r requirements.txt && pm2 reload ecosystem.config.js --env production && pip list'
    }
  }
};
