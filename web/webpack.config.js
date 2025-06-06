const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const TerserPlugin = require('terser-webpack-plugin');

module.exports = (env, argv) => {
  const isProd = false; //argv.mode === 'production';

  return {
    output: {
      path: path.resolve(__dirname, 'dist'),
      filename: isProd ? 'bundle.[contenthash].js' : 'bundle.js',
      clean: true,
    },
    module: {
      rules: [
        // {test: /\.css$/, use: ['style-loader', 'css-loader']},
        {test: /\.css$/, use: [MiniCssExtractPlugin.loader, 'css-loader']},
        {test: /\.(json|png|jpe?g|gif|webp)$/, type: 'asset/resource', generator: {filename: '[name][ext]'},},
      ],
    },
    plugins: [
      new HtmlWebpackPlugin({
        template: './src/index.html',
        filename: 'index.html',
      }),
      new MiniCssExtractPlugin({
        filename: isProd ? 'style.[contenthash].css' : 'style.css',
      }),
    ], optimization: {
      minimizer: [new TerserPlugin({
        terserOptions: {
          compress: {drop_console: isProd},
        },
      })],
    }
  };
};
