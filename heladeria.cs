using System;
using System.Data.SQLite;
using System.Windows.Forms;

namespace HeladeriaPOS
{
    public partial class MainForm : Form
    {
        private SQLiteConnection connection;

        public MainForm()
        {
            InitializeComponent();
            InitializeDatabase();
            LoadStock();
        }

        private void InitializeDatabase()
        {
            string dbPath = "Data Source=heladeria.db;";
            connection = new SQLiteConnection(dbPath);
            connection.Open();

            string createProductTable = @"CREATE TABLE IF NOT EXISTS productos (
                                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                                            nombre TEXT NOT NULL UNIQUE,
                                            precio REAL NOT NULL CHECK(precio > 0),
                                            stock INTEGER NOT NULL CHECK(stock >= 0),
                                            stock_minimo INTEGER NOT NULL CHECK(stock_minimo >= 0)
                                        );";

            string createInformeTable = @"CREATE TABLE IF NOT EXISTS informes (
                                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                                            fecha TIMESTAMP NOT NULL,
                                            tipo TEXT NOT NULL,
                                            contenido TEXT NOT NULL
                                        );";

            ExecuteNonQuery(createProductTable);
            ExecuteNonQuery(createInformeTable);
        }

        private void LoadStock()
        {
            string query = "SELECT id, nombre, precio, stock, stock_minimo FROM productos;";
            var command = new SQLiteCommand(query, connection);
            var reader = command.ExecuteReader();

            while (reader.Read())
            {
                // Process each product
                int id = Convert.ToInt32(reader["id"]);
                string nombre = reader["nombre"].ToString();
                double precio = Convert.ToDouble(reader["precio"]);
                int stock = Convert.ToInt32(reader["stock"]);
                int stockMin = Convert.ToInt32(reader["stock_minimo"]);

                // Populate a UI component like DataGridView (placeholder example)
                Console.WriteLine($"{id} - {nombre} - {precio:C} - {stock} - Min: {stockMin}");
            }

            reader.Close();
        }

        private void ExecuteNonQuery(string query)
        {
            using var command = new SQLiteCommand(query, connection);
            command.ExecuteNonQuery();
        }

        private void OnAddProduct(object sender, EventArgs e)
        {
            try
            {
                string nombre = txtNombre.Text.Trim();
                double precio = Convert.ToDouble(txtPrecio.Text);
                int stock = Convert.ToInt32(txtStock.Text);
                int stockMin = Convert.ToInt32(txtStockMin.Text);

                string insertQuery = @"INSERT INTO productos (nombre, precio, stock, stock_minimo) 
                                      VALUES (@nombre, @precio, @stock, @stockMin);";

                using var command = new SQLiteCommand(insertQuery, connection);
                command.Parameters.AddWithValue("@nombre", nombre);
                command.Parameters.AddWithValue("@precio", precio);
                command.Parameters.AddWithValue("@stock", stock);
                command.Parameters.AddWithValue("@stockMin", stockMin);

                command.ExecuteNonQuery();

                MessageBox.Show("Producto agregado exitosamente.", "Éxito", MessageBoxButtons.OK, MessageBoxIcon.Information);
                LoadStock();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error al agregar producto: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void OnDeleteProduct(object sender, EventArgs e)
        {
            try
            {
                int id = Convert.ToInt32(txtProductId.Text);

                string deleteQuery = "DELETE FROM productos WHERE id = @id;";

                using var command = new SQLiteCommand(deleteQuery, connection);
                command.Parameters.AddWithValue("@id", id);

                command.ExecuteNonQuery();

                MessageBox.Show("Producto eliminado exitosamente.", "Éxito", MessageBoxButtons.OK, MessageBoxIcon.Information);
                LoadStock();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error al eliminar producto: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void OnExit(object sender, EventArgs e)
        {
            connection.Close();
            Application.Exit();
        }
    }

    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }
    }
}
