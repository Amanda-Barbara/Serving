# CTRԤ��ģ��

## 1. ����

���������Ƽ������߹���ҵ�񳡾��У�embedding�����Ĺ�ģ�����ǳ��Ӵ󣬴ﵽ����GB����T����ѵ����˹�ģ��ģ����Ҫ�õ�����ֲ�ʽѵ����������������Ƭ���ºͱ��棻��һ���棬ѵ���õ�ģ�ͣ�ҪӦ��������ҵ��Ҳ���Ե������ء�Paddle Serving�ṩ���ģϡ�������д�����û����Է���ؽ������ģ��ϡ�������kv��ʽ�йܵ�������������Ԥ��ֻ�轫����Ҫ�Ĳ����Ӽ��Ӳ��������ȡ��������ִ�к�����Ԥ�����̡�

������CTRԤ��ģ��Ϊ������ʾPaddle Serving�����ʹ�ô��ģϡ��������񡣹���ģ��ϸ����ο�[ԭʼģ��](https://github.com/PaddlePaddle/models/tree/v1.5/PaddleRec/ctr)

����[�����ݼ�������](https://www.kaggle.com/c/criteo-display-ad-challenge/data)����ģ��ԭʼ����Ϊ13άinteger features��26άcategorical features�������ǵ�ģ���У�13άinteger feature��Ϊdense feature����feed��һ��data layer����26άcategorical features������Ϊһ��feature�ֱ�feed��һ��data layer������֮�⣬Ϊ����aucָ�꣬����label��Ϊһ��feature���롣

����ȱʡѵ����������ģ�͵�embedding dimΪ100w��sizeΪ10��Ҳ���ǲ�������Ϊ1000000 x 10��float�;���ʵ��ռ���ڴ湲1000000 x 10 x sizeof(float) = 39MB��**ʵ�ʳ����У�embedding����Ҫ��Ķࣻ��˸�demo��Ϊ��ʾʹ��**��


## 2. ģ�Ͳü�

��д���ĵ�ʱ([v1.5](https://github.com/PaddlePaddle/models/tree/v1.5))��ѵ���ű���PaddlePaddle py_reader����������ȡ�ٶȣ�program�д���py_reader���OP����ѵ��������ֻ������ģ�Ͳ�����û�б���program������Ĳ���û��ֱ����Ԥ�����أ�����ԭʼ���������������tensor��auc��batch_auc����ʵ��ģ������Ԥ��ʱֻ��Ҫÿ��������predict����Ҫ�ĵ�ģ�͵����tensorΪpredict�����У�Ϊ����ʾϡ����������ʹ�ã�����Ҫ���⽫embedding layer������lookup_table OP��Ԥ��program���õ�����embedding layer��output variable��Ϊ��������룬Ȼ������Ӷ�Ӧ��feed OP��ʹ�������ܹ���Ԥ��ʱ��ϡ����������ȡ��embedding�����󣬽�����ֱ��feed������embedding��output variable��

�������ϼ����濼�ǣ�������Ҫ��ԭʼprogram���вü������¹���Ϊ��

1) ȥ��py_reader��ش��룬��Ϊ��fluid�Դ���reader��DataFeed
2) �޸�ԭʼ�������ã���predict������Ϊfetch target
3) �޸�ԭʼ�������ã���26��ϡ�������embedding layer��output��Ϊfeed target���������ϡ������������ʹ��
4) �޸ĺ�����磬����train 1��batch�󣬵���`fluid.io.save_inference_model()`����òü����ģ��program
5) �ü����program����python�ٴδ���ȥ��embedding layer��lookup_table OP��������Ϊ����ǰPaddle Fluid�ڵ�4��`save_inference_model()`ʱû�вü��ɾ�����������embedding��lookup_table OP�������ЩOP��ȥ��������ôembedding��output variable�ͻ���2������OP��һ����feed OP������Ҫ��ӵģ���һ����lookup_table����lookup_table��û�����룬�����������feed OP��������า�ǣ����´���
6) ��4���õ���program����ֲ�ʽѵ�������ģ�Ͳ�������embedding֮�⣩���浽һ���γ�������Ԥ��ģ��

��1) - ��5)���ü���Ϻ��ģ�������������£�

![Pruned CTR prediction network](doc/pruned-ctr-network.png)


�����ü����̾���˵�����£�

### 2.1 ����������ȥ��py_reader

Inference program����ctr_dnn_model()����ʱ���`user_py_reader=False`�����������ctr_dnn_model�����н�py_reader��صĴ���ȥ��

�޸�ǰ��
```python
def train():
    args = parse_args()

    if not os.path.isdir(args.model_output_dir):
        os.mkdir(args.model_output_dir)

    loss, auc_var, batch_auc_var, py_reader, _ = ctr_dnn_model(args.embedding_size, args.sparse_feature_dim)
    ...
```

�޸ĺ�
```python
def train():
    args = parse_args()

    if not os.path.isdir(args.model_output_dir):
        os.mkdir(args.model_output_dir)

    loss, auc_var, batch_auc_var, py_reader, _ = ctr_dnn_model(args.embedding_size, args.sparse_feature_dim, use_py_reader=False)
    ...
```


### 2.2 �����������޸�feed targets��fetch targets

���2�ڿ�ͷ������Ϊ��ʹprogram�ʺ�����ʾϡ�������ʹ�ã�����Ҫ�ü�program����`ctr_dnn_model`��feed variable list��fetch variable�ֱ�ĵ���

1) Inference program��26άϡ�������������Ϊÿ��������embedding layer��output variable
2) fetch targets�з��ص���predict��ȡ��auc_var��batch_auc_var

����д����ʱ��ԭʼ���������� (network_conf.py��)`ctr_dnn_model`�������£�

```python
def ctr_dnn_model(embedding_size, sparse_feature_dim, use_py_reader=True):

    def embedding_layer(input):
        emb = fluid.layers.embedding(
            input=input,
            is_sparse=True,
            # you need to patch https://github.com/PaddlePaddle/Paddle/pull/14190
            # if you want to set is_distributed to True
            is_distributed=False,
            size=[sparse_feature_dim, embedding_size],
            param_attr=fluid.ParamAttr(name="SparseFeatFactors",
                                       initializer=fluid.initializer.Uniform()))
        return fluid.layers.sequence_pool(input=emb, pool_type='average')    # ���޸�1

    dense_input = fluid.layers.data(
        name="dense_input", shape=[dense_feature_dim], dtype='float32')

    sparse_input_ids = [
        fluid.layers.data(name="C" + str(i), shape=[1], lod_level=1, dtype='int64')
        for i in range(1, 27)]

    label = fluid.layers.data(name='label', shape=[1], dtype='int64')

    words = [dense_input] + sparse_input_ids + [label]

    py_reader = None
    if use_py_reader:
        py_reader = fluid.layers.create_py_reader_by_data(capacity=64,
                                                          feed_list=words,
                                                          name='py_reader',
                                                          use_double_buffer=True)
        words = fluid.layers.read_file(py_reader)

    sparse_embed_seq = list(map(embedding_layer, words[1:-1]))              # ���޸�2
    concated = fluid.layers.concat(sparse_embed_seq + words[0:1], axis=1)

    fc1 = fluid.layers.fc(input=concated, size=400, act='relu',
                          param_attr=fluid.ParamAttr(initializer=fluid.initializer.Normal(
                              scale=1 / math.sqrt(concated.shape[1]))))
    fc2 = fluid.layers.fc(input=fc1, size=400, act='relu',
                          param_attr=fluid.ParamAttr(initializer=fluid.initializer.Normal(
                              scale=1 / math.sqrt(fc1.shape[1]))))
    fc3 = fluid.layers.fc(input=fc2, size=400, act='relu',
                          param_attr=fluid.ParamAttr(initializer=fluid.initializer.Normal(
                              scale=1 / math.sqrt(fc2.shape[1]))))
    predict = fluid.layers.fc(input=fc3, size=2, act='softmax',
                              param_attr=fluid.ParamAttr(initializer=fluid.initializer.Normal(
                                  scale=1 / math.sqrt(fc3.shape[1]))))

    cost = fluid.layers.cross_entropy(input=predict, label=words[-1])
    avg_cost = fluid.layers.reduce_sum(cost)
    accuracy = fluid.layers.accuracy(input=predict, label=words[-1])
    auc_var, batch_auc_var, auc_states = \
        fluid.layers.auc(input=predict, label=words[-1], num_thresholds=2 ** 12, slide_steps=20)

    return avg_cost, auc_var, batch_auc_var, py_reader, words              # ���޸�3
```

�޸ĺ�

```python
def ctr_dnn_model(embedding_size, sparse_feature_dim, use_py_reader=True):
    def embedding_layer(input):
        emb = fluid.layers.embedding(
            input=input,
            is_sparse=True,
            # you need to patch https://github.com/PaddlePaddle/Paddle/pull/14190
            # if you want to set is_distributed to True
            is_distributed=False,
            size=[sparse_feature_dim, embedding_size],
            param_attr=fluid.ParamAttr(name="SparseFeatFactors",
                                       initializer=fluid.initializer.Uniform()))
        seq = fluid.layers.sequence_pool(input=emb, pool_type='average')
        return emb, seq                                                   # ��Ӧ�����޸Ĵ�1
    dense_input = fluid.layers.data(
        name="dense_input", shape=[dense_feature_dim], dtype='float32')
    sparse_input_ids = [
        fluid.layers.data(name="C" + str(i), shape=[1], lod_level=1, dtype='int64')
        for i in range(1, 27)]
    label = fluid.layers.data(name='label', shape=[1], dtype='int64')
    words = [dense_input] + sparse_input_ids + [label]
    sparse_embed_and_seq = list(map(embedding_layer, words[1:-1]))
    
    emb_list = [x[0] for x in sparse_embed_and_seq]                       # ��Ӧ�����޸Ĵ�2
    sparse_embed_seq = [x[1] for x in sparse_embed_and_seq]
    
    concated = fluid.layers.concat(sparse_embed_seq + words[0:1], axis=1)
    
    train_feed_vars = words                                              # ��Ӧ�����޸Ĵ�2
    inference_feed_vars = emb_list + words[0:1]
    
    fc1 = fluid.layers.fc(input=concated, size=400, act='relu',
                          param_attr=fluid.ParamAttr(initializer=fluid.initializer.Normal(
                              scale=1 / math.sqrt(concated.shape[1]))))
    fc2 = fluid.layers.fc(input=fc1, size=400, act='relu',
                          param_attr=fluid.ParamAttr(initializer=fluid.initializer.Normal(
                              scale=1 / math.sqrt(fc1.shape[1]))))
    fc3 = fluid.layers.fc(input=fc2, size=400, act='relu',
                          param_attr=fluid.ParamAttr(initializer=fluid.initializer.Normal(
                              scale=1 / math.sqrt(fc2.shape[1]))))
    predict = fluid.layers.fc(input=fc3, size=2, act='softmax',
                              param_attr=fluid.ParamAttr(initializer=fluid.initializer.Normal(
                                  scale=1 / math.sqrt(fc3.shape[1]))))
    cost = fluid.layers.cross_entropy(input=predict, label=words[-1])
    avg_cost = fluid.layers.reduce_sum(cost)
    accuracy = fluid.layers.accuracy(input=predict, label=words[-1])
    auc_var, batch_auc_var, auc_states = \
        fluid.layers.auc(input=predict, label=words[-1], num_thresholds=2 ** 12, slide_steps=20)
    fetch_vars = [predict]
    
    # ��Ӧ�����޸Ĵ�3
    return avg_cost, auc_var, batch_auc_var, train_feed_vars, inference_feed_vars, fetch_vars
```

˵����

1) �޸Ĵ�1�����ǽ�embedding layer�������������
2) �޸Ĵ�2�����ǽ�embedding layer������������浽`emb_list`�����߽�һ�����浽`inference_feed_vars`������������`save_inference_model()`ʱָ��feed variable list��
3) �޸Ĵ�3�����ǽ�`words`������Ϊѵ��ʱ��feed variable list (`train_feed_vars`)����embedding layer��output variable��Ϊinferʱ��feed variable list (`inference_feed_vars`)����`predict`��Ϊfetch target (`fetch_vars`)���ֱ𷵻ء�`inference_feed_vars`��`fetch_vars`����`fluid.io.save_inference_model()`ʱָ��feed variable list��fetch target list


### 2.3 fluid.io.save_inference_model()����ü����program

`fluid.io.save_inference_model()`��������ģ�Ͳ��������ܹ�����feed variable list��fetch target list��������program���вü����γ��ʺ�inference�õ�program������ԭ���ǣ�����ǰ���������ã���fetch target list��ʼ�������������������OP�б�����ÿ��OP���������Ŀ��variable list���ٴεݹ�ط����ҵ���������OP��variable list��

��2.2���������Ѿ��õ������`inference_feed_vars`��`fetch_vars`��������ֻҪ��ѵ��������ÿ�α���ģ�Ͳ���ʱ��Ϊ����`fluid.io.save_inference_model()`��

�޸�ǰ��

```python
def train_loop(args, train_program, py_reader, loss, auc_var, batch_auc_var,
               trainer_num, trainer_id):
    
...ʡ��
    for pass_id in range(args.num_passes):
        pass_start = time.time()
        batch_id = 0
        py_reader.start()

        try:
            while True:
                loss_val, auc_val, batch_auc_val = pe.run(fetch_list=[loss.name, auc_var.name, batch_auc_var.name])
                loss_val = np.mean(loss_val)
                auc_val = np.mean(auc_val)
                batch_auc_val = np.mean(batch_auc_val)

                logger.info("TRAIN --> pass: {} batch: {} loss: {} auc: {}, batch_auc: {}"
                      .format(pass_id, batch_id, loss_val/args.batch_size, auc_val, batch_auc_val))
                if batch_id % 1000 == 0 and batch_id != 0:
                    model_dir = args.model_output_dir + '/batch-' + str(batch_id)
                    if args.trainer_id == 0:
                        fluid.io.save_persistables(executor=exe, dirname=model_dir,
                                                   main_program=fluid.default_main_program())
                batch_id += 1
        except fluid.core.EOFException:
            py_reader.reset()
        print("pass_id: %d, pass_time_cost: %f" % (pass_id, time.time() - pass_start))
...ʡ��
```

�޸ĺ�

```python
def train_loop(args,
               train_program,
               train_feed_vars,
               inference_feed_vars,  # �ü�program�õ�feed variable list
               fetch_vars,           # �ü�program�õ�fetch variable list
               loss,
               auc_var,
               batch_auc_var,
               trainer_num,
               trainer_id):
    # ��Ϊ�Ѿ���py_readerȥ����������fluid�Դ���DataFeeder
    dataset = reader.CriteoDataset(args.sparse_feature_dim)
    train_reader = paddle.batch(
        paddle.reader.shuffle(
            dataset.train([args.train_data_path], trainer_num, trainer_id),
            buf_size=args.batch_size * 100),
        batch_size=args.batch_size)
    
    inference_feed_var_names = [var.name for var in inference_feed_vars]
    
    place = fluid.CPUPlace()
    exe = fluid.Executor(place)
    exe.run(fluid.default_startup_program())
    total_time = 0
    pass_id = 0
    batch_id = 0

    feed_var_names = [var.name for var in feed_vars]
    feeder = fluid.DataFeeder(feed_var_names, place)

    for data in train_reader():
        loss_val, auc_val, batch_auc_val = exe.run(fluid.default_main_program(),
                                            feed = feeder.feed(data),
                                            fetch_list=[loss.name, auc_var.name, batch_auc_var.name])
        fluid.io.save_inference_model(model_dir,
                                      inference_feed_var_names,
                                      fetch_vars,
                                      exe,
                                      fluid.default_main_program())
        break # ����ֻҪ�ü����program������Ҫģ�Ͳ��������ֻtrainһ��batch��ֹͣ��
    loss_val = np.mean(loss_val)
    auc_val = np.mean(auc_val)
    batch_auc_val = np.mean(batch_auc_val)
    logger.info("TRAIN --> pass: {} batch: {} loss: {} auc: {}, batch_auc: {}"
                      .format(pass_id, batch_id, loss_val/args.batch_size, auc_val, batch_auc_val))
```

### 2.4 ��python�ٴδ���inference program��ȥ��lookup_table OP

��һ������Ϊ`fluid.io.save_inference_model()`�ü�����programû�н�lookup_table OPȥ����δ�����`save_inference_model`�ӿ����ƣ����ڿ�����

��Ҫ���룺

```python
ef prune_program():
    # �Ӵ��̶���inference program
    args = parse_args()
    model_dir = args.model_output_dir + "/inference_only"
    model_file = model_dir + "/__model__"
    with open(model_file, "rb") as f:
        protostr = f.read()
    f.close()
    
    # �����л�Ϊprotobuf message
    proto = framework_pb2.ProgramDesc.FromString(six.binary_type(protostr))
    
    # ��������OP��ȥ��lookup_table
    block = proto.blocks[0]
    kept_ops = [op for op in block.ops if op.type != "lookup_table"]
    del block.ops[:]
    block.ops.extend(kept_ops)
    
    # �����޸ĺ��program
    with open(model_file + ".pruned", "wb") as f:
        f.write(proto.SerializePartialToString())
    f.close()
```
### 2.5 �ü����̴���һ��

�����ṩ�������Ĳü�CTRԤ��ģ�͵Ľű��ļ�save_program.py��ͬ[CTR�ֲ�ʽѵ������](doc/DISTRIBUTED_TRAINING_AND_SERVING.md)һ�𷢲���������trainer��pserver������ѵ���ű�Ŀ¼���ҵ�

## 3. ����Ԥ���������

Client�ˣ�
1) Dense feature: ��datasetÿ��������ȡ13��integer features���γ�1��dense feature
2) Sparse feature: ��datasetÿ��������ȡ26��categorical feature���ֱ𾭹�hash(str(feature_index) + feature_string)ǩ�����õ�ÿ��feature��id���γ�26��sparse feature

Serving��:
1) Dense feature: dense feature��13��float�����֣�һ��feed������dense_input���variable��Ӧ��LodTensor
2) Sparse feature: 26��sparse feature id���ֱ����kv�����ȡ��Ӧ��embedding������feed����Ӧ��26��embedding layer��output variable�������ǲü������������У���Щvariable�ֱ��Ӧ�ı�����Ϊembedding_0.tmp_0, embedding_1.tmp_0, ... embedding_25.tmp_0
3) ִ��Ԥ�⣬��ȡԤ������
