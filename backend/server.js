import app from './app.js';

const PORT = Number(process.env.PORT || 8787);

app.listen(PORT, () => {
  console.log(`Backend auth TPV Elite escuchando en http://localhost:${PORT}`);
});
