# pylint: disable=C0111,too-many-arguments,too-many-instance-attributes,too-many-locals,redefined-outer-name,fixme
# pylint: disable=superfluous-parens, no-member, invalid-name
import sys
sys.path.insert(0, "../../python")
import mxnet as mx
from lstm import lstm_unroll
from bucket_io import BucketSentenceIter, default_build_vocab

# def Perplexity(label, pred):
#     loss = 0.
#     for i in range(pred.shape[0]):
#         a = min(label[i])
#         b = max(label[i])
#         c = min(pred[i])
#         d = max(pred[i])
#         for j in range(pred.shape[1]):
#             pred_normal = (d-c)/(b-a)*(pred[i][j]-a)+c
#             loss += (pred_normal - label[i][j])*(pred_normal - label[i][j])
#     return loss/pred.shape[0]
def Perplexity(label, pred):
    loss = 0.
    global num
    for i in range(pred.shape[0]):
        for j in range(pred.shape[1]):
            loss += (pred[i][j] - label[i][j])*(pred[i][j] - label[i][j])
    return loss/pred.shape[0]
if __name__ == '__main__':
    batch_size = 1
    buckets = 30
    num_hidden = 2500
    num_label = 1500
    num_lstm_layer = 4
    num_epoch = 500
    learning_rate = 0.5
    momentum = 0.0
    print(batch_size, buckets, num_hidden, num_lstm_layer, num_epoch, learning_rate)
    contexts = [mx.context.gpu(0)]
    img_data,wave_data = default_build_vocab("./data/data/1.mp4", "./data/data/1.mp3")
    ngpu = 2
    # A simple two GPU placement plan
    group2ctx = {'embed': mx.gpu(0),
                 'decode': mx.gpu(ngpu - 1)}

    for i in range(num_lstm_layer):
        group2ctx['layer%d' % i] = mx.gpu(i * ngpu // num_lstm_layer)
        #group2ctx['layer%d' % i] = mx.gpu(1)


    def sym_gen(seq_len):
        return lstm_unroll(num_lstm_layer, seq_len, len(img_data),
                           num_hidden=num_hidden, num_label=num_label)

    init_c = [('l%d_init_c'%l, (batch_size, num_hidden)) for l in range(num_lstm_layer)]
    init_h = [('l%d_init_h'%l, (batch_size, num_hidden)) for l in range(num_lstm_layer)]
    init_states = init_c + init_h

    data_train = BucketSentenceIter(img_data,wave_data,
                                    buckets, batch_size, init_states, num_label)

    symbol = sym_gen(buckets)
    model = mx.model.FeedForward(ctx=contexts,
                                 symbol=symbol,
                                 num_epoch=num_epoch,
                                 learning_rate=learning_rate,
                                 momentum=momentum,
                                 wd=0.00001,
                                 initializer=mx.init.Xavier(factor_type="in", magnitude=2.34))
    import logging
    head = '%(asctime)-15s %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=head)

    model.fit(X=data_train, eval_data=None,group2ctx=group2ctx,
              eval_metric=mx.metric.np(Perplexity),
              batch_end_callback=mx.callback.Speedometer(batch_size, 50),
              epoch_end_callback = mx.callback.do_checkpoint('model/lip'))


    #
    # init_c = [('l%d_init_c'%l, (batch_size, num_hidden)) for l in range(num_lstm_layer)]
    # init_h = [('l%d_init_h'%l, (batch_size, num_hidden)) for l in range(num_lstm_layer)]
    # init_states = init_c + init_h
    #
    # data_train = BucketSentenceIter(img_data,wave_data,
    #                                 buckets, batch_size, init_states, num_label)
    # state_names = [x[0] for x in init_states]
    # def sym_gen(seq_len):
    #     sym =  lstm_unroll(num_lstm_layer, seq_len, len(img_data),
    #                        num_hidden=num_hidden, num_label=num_label)
    #     data_names = [('data/%d'%l) for l in range(buckets)] + state_names
    #     label_names = [('label/%d'%l) for l in range(buckets)]
    #     return (sym, data_names, label_names)
    #
    #
    # mod = mx.mod.Module(*sym_gen(buckets), context=contexts)
    # import logging
    # head = '%(asctime)-15s %(message)s'
    # logging.basicConfig(level=logging.DEBUG, format=head)
    #
    # mod.fit(data_train, eval_data=None, num_epoch=num_epoch,
    #         eval_metric=mx.metric.np(Perplexity),
    #         batch_end_callback=mx.callback.Speedometer(batch_size, 50),
    #         initializer=mx.init.Xavier(factor_type="in", magnitude=2.34),
    #         optimizer='sgd',
    #         optimizer_params={'learning_rate':0.01, 'momentum': 0.9, 'wd': 0.00001})



    # mod = mx.mod.Module(*sym_gen(buckets), context=contexts)
    # mod.bind(data_shapes=data_train.provide_data, label_shapes=data_train.provide_label)
    # mod.init_params()
    #
    # mod.init_optimizer(optimizer_params={'learning_rate':1, 'momentum': 0.9})
    # metric = mx.metric.np(Perplexity)
    #
    # for i_epoch in range(num_epoch):
    #     for i_iter, batch in enumerate(data_train):
    #         mod.forward(batch)
    #         mod.update_metric(metric, batch.label)
    #         mod.backward()
    #         mod.update()
    #
    #     for name, val in metric.get_name_value():
    #         print('epoch %03d: %s=%f' % (i_epoch, name, val))
    #     metric.reset()
    #     data_train.reset()



